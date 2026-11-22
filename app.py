import os
import psycopg
from database import get_db_connection
from mistakes import learner_mistakes
from email_presentation import present_email
from performance import session_results, learner_history, complete_training_session
from adaptive import (VERSION, PAIR_VERSIONS, balanced_session_scenarios,
                      balanced_plan_safe, evaluate_session, ControlScheduleUnavailable,
                      next_scenario, sequence_enforced, pair_safe)
from psycopg.types.json import Jsonb
from dotenv import load_dotenv
import time
import secrets
import math
from participant_refs import item_reference, resolve_reference
from security import database_id, valid_registration, MAX_PASSWORD_LENGTH, MAX_EMAIL_LENGTH, tokens_match
from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("PHISHSENSE_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set PHISHSENSE_SECRET_KEY before starting PhishSense.")

app.config.update(
    MAX_CONTENT_LENGTH=64 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("PHISHSENSE_HTTPS", "").lower() == "true",
)

SESSION_EMAIL_LIMIT = 10


@app.after_request
def security_headers(response):
    # Session signatures provide integrity, not secrecy: never serialize item plans.
    session.pop("training_scenario_ids", None)
    session.pop("active_scenario_id", None)
    # Email content is plain text. No scripts, frames, plug-ins or remote resources.
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'none'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self'; font-src 'self'; connect-src 'self'; frame-src 'none'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.context_processor
def auth_actions():
    if "auth_form_token" not in session:
        session["auth_form_token"] = secrets.token_urlsafe(32)
    return {"auth_form_token": session["auth_form_token"], "present_email": present_email,
            "training_item_url": training_item_url}


@app.before_request
def validate_forms():
    if request.method != "POST":
        return None
    # Reject ambiguous duplicate fields before a route chooses one interpretation.
    if any(len(request.form.getlist(key)) != 1 for key in request.form):
        return "Ambiguous form fields.", 400
    if request.endpoint in {"login", "register", "logout"}:
        expected = session.get("auth_form_token")
        actual = request.form.get("auth_form_token", "")
        if not expected or not tokens_match(actual, expected):
            return "Invalid or expired account form. Reload the page and try again.", 400
    return None


def login_required():
    return "user_id" in session


def training_item_ref(scenario_id):
    if "training_nonce" not in session:
        session["training_nonce"] = secrets.token_urlsafe(24)
    return item_reference(app.secret_key, session["user_id"],
        session["training_session_id"], scenario_id, session["training_nonce"])


def training_item_url(scenario_id):
    return url_for("training", item_ref=training_item_ref(scenario_id))


def resolve_training_item(reference, ids):
    return resolve_reference(app.secret_key, session["user_id"],
        session.get("training_session_id"), ids, session.get("training_nonce"), reference)


def get_reviewed_ids(conn, training_session_id):
    rows = conn.execute(
        """
        SELECT DISTINCT scenario_id
        FROM training_responses
        WHERE session_id = %s
        """,
        (training_session_id,)
    ).fetchall()

    return {row["scenario_id"] for row in rows}


def get_active_training_session(conn, lock=False):
    training_session_id = session.get("training_session_id")

    if training_session_id is None:
        return None

    row = conn.execute(
        """
        SELECT *
        FROM training_sessions
        WHERE session_id = %s
          AND user_id = %s
          AND session_type = 'training'
        """ + (" FOR UPDATE" if lock else ""),
        (training_session_id, session["user_id"])
    ).fetchone()
    if row and row['scenario_ids'] is not None:
        session['training_scenario_ids'] = row['scenario_ids']
    return row


def create_training_session(conn):
    learner = conn.execute('SELECT study_group FROM users WHERE user_id=%s FOR SHARE',
                           (session['user_id'],)).fetchone()
    scenario_ids = balanced_session_scenarios(conn, session['user_id'], learner['study_group'])

    if not scenario_ids:
        return None
    if len(scenario_ids) != SESSION_EMAIL_LIMIT or not pair_safe(conn, scenario_ids):
        raise ControlScheduleUnavailable()

    cursor = conn.execute(
        """
        INSERT INTO training_sessions (
            user_id,
            session_type,
            current_difficulty, study_group, algorithm_version, scenario_ids
        )
        SELECT user_id, 'training', 'intermediate', study_group, %s, %s
        FROM users WHERE user_id=%s RETURNING session_id
        """,
        (VERSION, Jsonb(scenario_ids), session["user_id"])
    )

    training_session_id = cursor.fetchone()["session_id"]
    conn.commit()

    session["training_session_id"] = training_session_id
    session["training_nonce"] = secrets.token_urlsafe(24)
    session["training_scenario_ids"] = scenario_ids
    session.pop("active_scenario_id", None)
    session.pop("active_item_ref", None)
    session.pop("scenario_started_at", None)
    session.pop("active_form_token", None)

    return training_session_id


def get_training_scenario_ids():
    scenario_ids = session.get("training_scenario_ids", [])

    if not isinstance(scenario_ids, list):
        return []

    if not all(type(scenario_id) is int for scenario_id in scenario_ids):
        return []

    return scenario_ids


@app.context_processor
def training_actions():
    if login_required() and "start_training_token" not in session:
        session["start_training_token"] = secrets.token_urlsafe(32)
    return {"start_training_token": session.get("start_training_token", "")}


@app.route("/training/start", methods=["POST"])
def start_training():
    if not login_required():
        return redirect(url_for("login"))
    token = session.get("start_training_token")
    if not token or not tokens_match(request.form.get("form_token", ""), token):
        return "Invalid or expired session action.", 400
    conn = get_db_connection()
    try:
        # Serialize starts; a double click cannot create two unfinished sessions.
        conn.execute("SELECT user_id FROM users WHERE user_id=%s FOR UPDATE", (session["user_id"],))
        current = get_active_training_session(conn)
        if current and current["completed_at"] is None and current["scenario_ids"] is not None:
            return redirect(url_for("inbox"))
        pending = conn.execute("""SELECT * FROM training_sessions WHERE user_id=%s
            AND session_type='training' AND completed_at IS NULL AND algorithm_version=ANY(%s)
            AND scenario_ids IS NOT NULL ORDER BY session_id DESC LIMIT 1""",
            (session["user_id"], ["rules-v1", "rules-v2-ordered-control", *PAIR_VERSIONS])).fetchone()
        if pending:
            session["training_session_id"] = pending["session_id"]
            session["training_scenario_ids"] = pending["scenario_ids"]
        else:
            try:
                if create_training_session(conn) is None:
                    return "No training scenarios are currently available.", 503
            except ControlScheduleUnavailable:
                return "Scheduled training is not available yet. Please contact the study coordinator.", 503
    finally:
        conn.close()
    return redirect(url_for("inbox"))


@app.route("/")
def home():
    return render_template(
        "home.html",
        logged_in=login_required(),
        username=session.get("username", "Learner")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not valid_registration(username, email, password):
            return "Enter a valid username, email, and password within the field limits.", 400

        password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (username, email, password_hash)
            )
            conn.commit()

        except psycopg.errors.UniqueViolation:
            return (
                '<h1>Registration Failed</h1>'
                '<p>That username or email is already registered.</p>'
                '<a href="/register">Try Again</a>'
            )

        finally:
            conn.close()

        return (
            '<h1>Registration Successful!</h1>'
            '<p>Your PhishSense account has been created.</p>'
            '<p><a href="/login">Log In</a></p>'
            '<p><a href="/">Return to Homepage</a></p>'
        )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if (not email or len(email) > MAX_EMAIL_LENGTH or "\x00" in email or
                not password or len(password) > MAX_PASSWORD_LENGTH or "\x00" in password):
            return "Invalid email or password.", 400

        conn = get_db_connection()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            ).fetchone()

        finally:
            conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return (
            '<h1>Login Failed</h1>'
            '<p>Invalid email or password.</p>'
            '<a href="/login">Try Again</a>'
        )

    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "GET":
        return render_template("logout.html")
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        history_data = learner_history(conn, session["user_id"])
    finally:
        conn.close()
    return render_template(
        "dashboard.html",
        username=session.get("username", "Learner"),
        history=history_data,
        latest=history_data["completed_sessions"][-1] if history_data["completed_sessions"] else None,
    )


@app.route("/inbox")
def inbox():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        training_session = get_active_training_session(conn)
        scenario_ids = get_training_scenario_ids()
        if training_session and training_session["scenario_ids"] is None:
            return render_template("inbox.html", username=session.get("username", "Learner"),
                emails=[], reviewed_ids=set(), reviewed_count=0, total_count=0,
                progress_percent=0, legacy_plan_missing=True,
                training_error="This historical session has no saved scenario plan. Its records are preserved; start a new session to continue training."), 409

        if (
            training_session is None
            or not scenario_ids
        ):
            try:
                training_session_id = create_training_session(conn)
            except ControlScheduleUnavailable:
                return render_template(
                    "inbox.html", username=session.get("username", "Learner"),
                    emails=[], reviewed_ids=set(), reviewed_count=0, total_count=0,
                    progress_percent=0,
                    training_error="Scheduled training is not available yet. Please contact the study coordinator."
                ), 503

            if training_session_id is None:
                return render_template(
                    "inbox.html",
                    username=session.get("username", "Learner"),
                    emails=[],
                    reviewed_ids=set(),
                    reviewed_count=0,
                    total_count=0,
                    progress_percent=0
                )

            training_session = get_active_training_session(conn)
            scenario_ids = get_training_scenario_ids()

        placeholders = ",".join("%s" for _ in scenario_ids)

        emails = conn.execute(
            f"""
            SELECT *
            FROM training_scenarios
            WHERE scenario_id IN ({placeholders})
            """,
            scenario_ids
        ).fetchall()

        email_lookup = {
            email["scenario_id"]: email
            for email in emails
        }

        ordered_emails = [
            email_lookup[scenario_id]
            for scenario_id in scenario_ids
            if scenario_id in email_lookup
        ]

        reviewed_ids = get_reviewed_ids(
            conn,
            training_session["session_id"]
        )

        total_count = len(ordered_emails)
        reviewed_count = sum(
            1
            for email in ordered_emails
            if email["scenario_id"] in reviewed_ids
        )

        progress_percent = (
            round((reviewed_count / total_count) * 100)
            if total_count > 0
            else 0
        )


    finally:
        conn.close()

    return render_template(
        "inbox.html",
        username=session.get("username", "Learner"),
        emails=ordered_emails,
        reviewed_ids=reviewed_ids,
        reviewed_count=reviewed_count,
        total_count=total_count,
        progress_percent=progress_percent,
        sequence_locked=sequence_enforced(training_session),
        next_scenario_id=next_scenario(training_session, reviewed_ids),
        training_session_id=training_session["session_id"]
    )


@app.route("/training", methods=["GET", "POST"])
def training():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        if "scenario_id" in request.args:
            return redirect(url_for("inbox"))
        reference = request.args.get("item_ref", "")
        if not reference:
            return redirect(url_for("inbox"))

        conn = get_db_connection()

        try:
            training_session = get_active_training_session(conn)

            if (
                training_session is None
                or training_session["completed_at"] is not None
            ):
                return redirect(url_for("inbox"))

            scenario_id = resolve_training_item(reference, get_training_scenario_ids())
            if scenario_id is None:
                return redirect(url_for("inbox"))

            reviewed_ids = get_reviewed_ids(
                conn,
                training_session["session_id"]
            )

            if sequence_enforced(training_session) and scenario_id != next_scenario(training_session, reviewed_ids):
                return redirect(url_for("inbox"))

            if scenario_id in reviewed_ids:
                return redirect(url_for("inbox"))

            scenario = conn.execute(
                """
                SELECT *
                FROM training_scenarios
                WHERE scenario_id = %s
                """,
                (scenario_id,)
            ).fetchone()

        finally:
            conn.close()

        if scenario is None:
            return redirect(url_for("inbox"))

        if session.get("active_item_ref") != reference:
            session["scenario_started_at"] = time.time()

        if not isinstance(
            session.get("scenario_started_at"),
            (int, float)
        ):
            session["scenario_started_at"] = time.time()

        session["active_item_ref"] = reference
        session["active_form_token"] = secrets.token_urlsafe(24)

        return render_template(
            "training.html",
            scenario=scenario,
            username=session.get("username", "Learner"),
            form_token=session["active_form_token"], item_ref=reference
        )

    try:
        user_answer = int(request.form.get("user_answer", ""))
        confidence_level = int(
            request.form.get("confidence_level", "")
        )

    except (ValueError, TypeError):
        return "Invalid training response.", 400

    reasoning = request.form.get("reasoning", "").strip()
    form_token = request.form.get("form_token", "")

    reference = request.form.get("item_ref", "")
    if "scenario_id" in request.form:
        return "Numeric scenario references are not accepted.", 400

    if user_answer not in (0, 1):
        return "Invalid classification.", 400

    if confidence_level not in range(1, 6):
        return "Confidence must be between 1 and 5.", 400

    if not reasoning:
        return "Please explain your classification.", 400

    if "\x00" in reasoning:
        return "Invalid explanation.", 400

    if len(reasoning) > 5000:
        return "Your explanation is too long.", 400

    if not reference or not tokens_match(reference, session.get("active_item_ref")):
        return "This training email is no longer active.", 400

    expected_token = session.get("active_form_token")

    if (
        not expected_token
        or not tokens_match(form_token, expected_token)
    ):
        return "Invalid or expired training form.", 400

    started_at = session.get("scenario_started_at")

    now = time.time()
    if (type(started_at) not in (int, float) or not math.isfinite(started_at)
            or started_at > now):
        return "Training start time is invalid. Reopen the email.", 400

    response_time = now - started_at

    conn = get_db_connection()

    try:
        training_session = get_active_training_session(conn, lock=True)

        if (
            training_session is None
            or training_session["completed_at"] is not None
        ):
            return "This training session is no longer active.", 400

        scenario_id = resolve_training_item(reference, get_training_scenario_ids())
        if scenario_id is None:
            return "This email is no longer part of your training session.", 400

        if training_session['algorithm_version'] in PAIR_VERSIONS and not pair_safe(conn, training_session['scenario_ids']):
            return "Training selection is unavailable. Please contact the study coordinator.", 409

        if training_session['algorithm_version'] == VERSION and not balanced_plan_safe(conn, training_session['scenario_ids']):
            return "Training selection is unavailable. Please contact the study coordinator.", 409

        reviewed_ids = get_reviewed_ids(
            conn,
            training_session["session_id"]
        )

        if sequence_enforced(training_session) and scenario_id != next_scenario(training_session, reviewed_ids):
            return "Please complete the next available email first.", 400

        if scenario_id in reviewed_ids:
            return redirect(url_for("inbox"))

        scenario = conn.execute(
            """
            SELECT *
            FROM training_scenarios
            WHERE scenario_id = %s
            """,
            (scenario_id,)
        ).fetchone()

        if scenario is None:
            return "Training scenario not found.", 404

        is_correct = int(
            user_answer == scenario["is_phishing"]
        )

        conn.execute(
            """
            INSERT INTO training_responses (
                session_id,
                scenario_id,
                user_answer,
                is_correct,
                reasoning,
                confidence_level,
                response_time,
                difficulty_at_response
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                training_session["session_id"],
                scenario_id,
                user_answer,
                is_correct,
                reasoning,
                confidence_level,
                response_time,
                scenario["difficulty_level"]
            )
        )

        updated_ids = evaluate_session(conn, training_session)
        complete = complete_training_session(conn, session["user_id"], training_session["session_id"],
                                  get_training_scenario_ids())
        conn.commit()
        if updated_ids is not None:
            session['training_scenario_ids'] = updated_ids

    finally:
        conn.close()

    session.pop("active_scenario_id", None)
    session.pop("active_item_ref", None)
    session.pop("scenario_started_at", None)
    session.pop("active_form_token", None)

    return render_template(
        "training_feedback.html",
        scenario=scenario,
        is_correct=bool(is_correct),
        user_answer=user_answer,
        confidence_level=confidence_level,
        reasoning=reasoning,
        training_session_id=training_session["session_id"],
        training_complete=complete
    )


@app.route("/mistakes", methods=["GET"])
def mistakes():
    if not login_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        summary = learner_mistakes(conn, session["user_id"])
    finally:
        conn.close()
    response = app.make_response(render_template(
        "mistakes.html", summary=summary,
        username=session.get("username", "Learner")))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/results")
def results():
    if not login_required():
        return redirect(url_for("login"))
    raw_id = request.args.get("session_id")
    if raw_id is not None:
        selected_id = database_id(raw_id)
        if selected_id is None:
            abort(400)
    else:
        selected_id = None
    conn = get_db_connection()
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        if selected_id is None:
            latest = conn.execute("""SELECT session_id FROM training_sessions
                WHERE user_id=%s AND session_type='training' AND completed_at IS NOT NULL
                ORDER BY completed_at DESC, session_id DESC LIMIT 1""", (session["user_id"],)).fetchone()
            selected_id = latest["session_id"] if latest else session.get("training_session_id")
        summary = session_results(conn, session["user_id"], selected_id) if selected_id else None
        if raw_id is not None and summary is None:
            abort(404)
    finally:
        conn.close()
    response = app.make_response(render_template("results.html", result=summary))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/history")
def history():
    if not login_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        history_data = learner_history(conn, session["user_id"])
    finally:
        conn.close()
    response = app.make_response(render_template("history.html", history=history_data))
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run()