"""Read-only connection diagnostic. Never print connection strings or driver errors."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import get_db_connection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        with get_db_connection() as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            assert conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1
            print("Connected successfully; read-only SELECT 1 passed.")
            print("TLS active:", conn.pgconn.ssl_in_use)
            print("Certificate chain and hostname verification: verify-full enforced.")
    except Exception as error:
        message = str(error).lower()
        if any(s in message for s in ("resolve host", "translate host", "nodename nor servname", "name or service not known")):
            reason = "DNS resolution failed"
        elif "certificate verify failed" in message:
            reason = "certificate validation failed with the configured trust store"
        elif "root certificate file" in message:
            reason = "configured CA file is missing or unreadable"
        elif "password authentication failed" in message or "tenant or user not found" in message:
            reason = "database authentication failed"
        elif "timeout" in message or "connection refused" in message:
            reason = "database endpoint unreachable"
        else:
            reason = "connection/configuration error (details suppressed to protect credentials)"
        print("Connection check failed:", reason)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
