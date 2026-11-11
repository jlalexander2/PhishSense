import secrets
import importlib
import os
from pathlib import Path
import uuid
from unittest.mock import MagicMock

import psycopg
from psycopg import sql
import pytest

import database


def test_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        database.get_db_connection()


def test_tls_enforced(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db?sslmode=disable")
    captured = {}
    def connect(url, **kwargs):
        captured.update(kwargs)
        return MagicMock()
    monkeypatch.setattr(database.psycopg, "connect", connect)
    database.get_db_connection()
    assert captured["sslmode"] == "verify-full"
    assert captured["prepare_threshold"] is None


@pytest.fixture
def postgres(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL required for real PostgreSQL/Supabase tests")
    monkeypatch.setenv("DATABASE_URL", url)
    original = database.get_db_connection
    namespace = "phishsense_test_" + uuid.uuid4().hex
    with original() as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(namespace)))
    def connect():
        conn = original()
        conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(namespace)))
        return conn
    try:
        with connect() as conn:
            conn.execute(Path("schema.sql").read_text())
        yield connect
    finally:
        with original() as admin:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(namespace)))


def test_workflow(postgres, monkeypatch):
    monkeypatch.setenv("PHISHSENSE_SECRET_KEY", secrets.token_hex(32))
    application = importlib.import_module("app")
    monkeypatch.setattr(application, "get_db_connection", postgres)
    application.app.config.update(TESTING=True)
    client = application.app.test_client()
    assert client.get("/inbox").status_code == 302
    assert client.post("/register", data={}).status_code == 400
    account = dict(username="learner", email="learner@example.invalid", password=secrets.token_urlsafe(24))
    assert b"Successful" in client.post("/register", data=account).data
    assert b"Failed" in client.post("/register", data=account).data
    assert b"Failed" in client.post("/login", data={**account, "password": "wrong"}).data
    assert client.post("/login", data=account).status_code == 302
    assert b"learner" in client.get("/dashboard").data
    assert b"No training emails" in client.get("/inbox").data
    import import_scenarios
    monkeypatch.setattr(import_scenarios, "get_db_connection", postgres)
    scenarios = [dict(source_id=f"synthetic-{i}", sender_name="Test sender",
                      sender_email="test@example.invalid", subject=f"Test {i}", email_body="Synthetic email",
                      is_phishing=i % 2, difficulty_level="intermediate", explanation="Synthetic explanation",
                      review_status="approved") for i in range(12)]
    import_scenarios.import_scenarios(scenarios)
    import_scenarios.import_scenarios(scenarios)
    with postgres() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM training_scenarios").fetchone()["n"] == 12
        user = conn.execute("SELECT * FROM users").fetchone()
        assert user["password_hash"] != account["password"]
    assert b"Evercrest Group" in client.get("/inbox").data
    with client.session_transaction() as state:
        ids = state["training_scenario_ids"]
        session_id = state["training_session_id"]
    assert len(ids) == 10
    assert client.get("/training?scenario_id=999999").status_code == 302
    for index, scenario_id in enumerate(ids):
        assert client.get(f"/training?scenario_id={scenario_id}").status_code == 200
        with client.session_transaction() as state:
            token = state["active_form_token"]
        with postgres() as conn:
            answer = conn.execute("SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s", (scenario_id,)).fetchone()["is_phishing"]
        payload = dict(scenario_id=scenario_id, user_answer=answer, reasoning="Synthetic reasoning", confidence_level=4, form_token=token)
        for invalid in ({"confidence_level": 6}, {"reasoning": ""}, {"form_token": "wrong"}, {"user_answer": 7}):
            assert client.post("/training", data={**payload, **invalid}).status_code == 400
        feedback = client.post("/training", data=payload)
        assert b"Correct Answer!" in feedback.data
        assert b"Synthetic explanation" in feedback.data
        assert b"Synthetic reasoning" in feedback.data
        assert client.post("/training", data=payload).status_code == 400
        inbox = client.get("/inbox")
        assert f"{index + 1} of 10 Emails Reviewed".encode() in inbox.data
    assert b"Training Complete!" in inbox.data
    with postgres() as conn:
        responses = conn.execute("SELECT * FROM training_responses").fetchall()
        assert len(responses) == 10
        assert all(r["confidence_level"] == 4 and r["is_correct"] == 1 and r["response_time"] >= 0 for r in responses)
        assert conn.execute("SELECT completed_at FROM training_sessions WHERE session_id=%s", (session_id,)).fetchone()["completed_at"] is not None
    client.get("/logout")
    assert client.get("/inbox").status_code == 302


def test_constraints_and_rollback(postgres):
    with pytest.raises(psycopg.errors.CheckViolation):
        with postgres() as conn:
            conn.execute("INSERT INTO users(username,email,password_hash) VALUES ('rollback','rollback@example.invalid','hash')")
            conn.execute("INSERT INTO training_sessions(user_id,session_type) SELECT user_id,'invalid' FROM users")
    with postgres() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] == 0
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with postgres() as conn:
            conn.execute("INSERT INTO training_sessions(user_id,session_type) VALUES (999,'training')")


def test_sqlite_migration(postgres, monkeypatch, tmp_path):
    import hashlib
    import sqlite3
    import migrate_sqlite
    source = tmp_path / "synthetic.db"
    with sqlite3.connect(source) as conn:
        conn.executescript(Path("tests/legacy_schema.sql").read_text())
        conn.execute("INSERT INTO users(user_id,username,email,password_hash) VALUES (42,'legacy','legacy@example.invalid','unchanged-hash')")
        conn.execute("INSERT INTO training_scenarios(scenario_id,sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,explanation) VALUES (55,'Test','test@example.invalid','Test','Body',1,'beginner','Explanation')")
        conn.execute("INSERT INTO training_sessions(session_id,user_id,session_type) VALUES (66,42,'training')")
        conn.execute("INSERT INTO training_responses(session_id,scenario_id,user_answer,is_correct,reasoning,confidence_level,response_time,difficulty_at_response) VALUES (66,55,1,1,'Legacy reasoning',5,1.5,'beginner')")
    before = hashlib.sha256(source.read_bytes()).digest()
    monkeypatch.setattr(migrate_sqlite, "get_db_connection", postgres)
    assert migrate_sqlite.migrate(source)["users"] == 1
    migrate_sqlite.migrate(source, apply=True)
    with postgres() as conn:
        user = conn.execute("SELECT * FROM users").fetchone()
        assert user["user_id"] == 42 and user["password_hash"] == "unchanged-hash"
        assert conn.execute("SELECT reasoning FROM training_responses").fetchone()["reasoning"] == "Legacy reasoning"
        assert conn.execute("INSERT INTO users(username,email,password_hash) VALUES ('next','next@example.invalid','hash') RETURNING user_id").fetchone()["user_id"] == 43
    with pytest.raises(ValueError, match="empty"):
        migrate_sqlite.migrate(source, apply=True)
    assert hashlib.sha256(source.read_bytes()).digest() == before


def test_import_rejects_unapproved_before_connect(monkeypatch):
    import import_scenarios
    def unexpected_connection():
        pytest.fail("Invalid dataset must not open a database connection")
    monkeypatch.setattr(import_scenarios, "get_db_connection", unexpected_connection)
    with pytest.raises(ValueError, match="validation"):
        import_scenarios.import_scenarios([{"source_id": "unapproved"}])


def test_sqlite_preview_is_read_only(tmp_path, monkeypatch):
    import hashlib
    import sqlite3
    import migrate_sqlite
    source = tmp_path / "preview.db"
    with sqlite3.connect(source) as conn:
        conn.executescript(Path("tests/legacy_schema.sql").read_text())
    before = hashlib.sha256(source.read_bytes()).digest()
    def unexpected_connection():
        pytest.fail("Preview must not connect to PostgreSQL")
    monkeypatch.setattr(migrate_sqlite, "get_db_connection", unexpected_connection)
    assert all(count == 0 for count in migrate_sqlite.migrate(source).values())
    assert hashlib.sha256(source.read_bytes()).digest() == before


def test_blank_trust_uses_system(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setenv("PGSSLROOTCERT", " ")
    captured = {}
    monkeypatch.setattr(database.psycopg, "connect", lambda *a, **kw: (captured.update(kw), MagicMock())[1])
    database.get_db_connection()
    assert captured["sslrootcert"] == "system"
    assert captured["sslmode"] == "verify-full"


def test_missing_explicit_ca_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setenv("PGSSLROOTCERT", str(tmp_path / "missing.crt"))
    monkeypatch.setattr(database.psycopg, "connect", lambda *a, **kw: pytest.fail("Must fail before connecting"))
    with pytest.raises(RuntimeError, match="root certificate file"):
        database.get_db_connection()


def test_response_time_precision(postgres):
    value = 1.2345678901234567
    with postgres() as conn:
        assert conn.execute("SELECT %s::double precision AS value", (value,)).fetchone()["value"] == value
