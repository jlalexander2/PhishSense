"""Read-only SQLite source -> empty PostgreSQL target, in one transaction."""
import argparse
import sqlite3
from pathlib import Path

from psycopg import sql
from database import get_db_connection

TABLES = {
    "users": "user_id",
    "training_scenarios": "scenario_id",
    "training_sessions": "session_id",
    "training_responses": "response_id",
}


def migrate(source, apply=False):
    source = Path(source).resolve(strict=True)
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as old:
        old.execute("PRAGMA query_only = ON")
        old.execute("BEGIN")
        if old.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        if old.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("SQLite contains broken relationships")
        counts = {table: old.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                  for table in TABLES}
        print("Source row counts:", counts)
        if not apply:
            print("Dry run: source only; no PostgreSQL connection or writes.")
            return counts
        with get_db_connection() as target:
            target.execute(sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(
                sql.SQL(", ").join(map(sql.Identifier, TABLES))))
            for table in TABLES:
                if target.execute(sql.SQL("SELECT 1 FROM {} LIMIT 1").format(
                        sql.Identifier(table))).fetchone():
                    raise ValueError("Target must be empty; no rows were copied")
            for table, primary_key in TABLES.items():
                cursor = old.execute(f'SELECT * FROM "{table}"')
                columns = [item[0] for item in cursor.description]
                statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table),
                    sql.SQL(", ").join(map(sql.Identifier, columns)),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns))
                with target.cursor() as writer:
                    for row in cursor:
                        writer.execute(statement, row)
                # Compare every field without printing hashes or personal data.
                expected = old.execute(f'SELECT * FROM "{table}" ORDER BY "{primary_key}"')
                actual = target.execute(sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
                    sql.SQL(", ").join(map(sql.Identifier, columns)),
                    sql.Identifier(table), sql.Identifier(primary_key)))
                for original in expected:
                    copied = actual.fetchone()
                    for column, value in zip(columns, original):
                        result = copied[column]
                        if hasattr(result, "isoformat") and isinstance(value, str):
                            from datetime import datetime, timezone
                            parsed = datetime.fromisoformat(value)
                            if parsed.tzinfo is None:
                                parsed = parsed.replace(tzinfo=timezone.utc)
                            value = parsed
                        if value != result:
                            raise ValueError(f"Verification failed in {table}.{column}")
                # Transactional sequence restart (unlike setval, rolls back on failure).
                next_id = target.execute(sql.SQL("SELECT COALESCE(MAX({}), 0) + 1 AS n FROM {}").format(
                    sql.Identifier(primary_key), sql.Identifier(table))).fetchone()["n"]
                target.execute(sql.SQL("ALTER TABLE {} ALTER COLUMN {} RESTART WITH {}").format(
                    sql.Identifier(table), sql.Identifier(primary_key), sql.Literal(next_id)))
        print("Copy committed and field values verified. SQLite source unchanged.")
        return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply and input("Type MIGRATE to copy to the empty PostgreSQL target: ") != "MIGRATE":
        raise SystemExit("Canceled")
    try:
        migrate(args.source, args.apply)
    except Exception:
        # Driver errors can contain account details or submitted row values.
        raise SystemExit("Migration failed; transaction rolled back. Review configuration and source compatibility privately.") from None
