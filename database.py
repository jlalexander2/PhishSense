"""Shared server-side PostgreSQL connections; never falls back to SQLite."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def get_db_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL to your Supabase PostgreSQL connection string.")
    root_cert = os.environ.get("PGSSLROOTCERT", "").strip() or "system"
    if root_cert == "system":
        if psycopg.pq.version() < 160000:
            raise RuntimeError("System CA trust requires libpq 16 or newer; configure a trusted CA file instead.")
    else:
        root_cert = str(Path(root_cert).expanduser().resolve())
        if not Path(root_cert).is_file():
            raise RuntimeError("Configured root certificate file is missing or unreadable. Set PGSSLROOTCERT to system or a trusted CA file.")
    conn = psycopg.connect(
        url,
        row_factory=dict_row,
        sslmode="verify-full",
        sslrootcert=root_cert,
        connect_timeout=10,
        prepare_threshold=None,
        # Preserve exact floating-point values when PostgreSQL returns text results.
        options="-c timezone=UTC -c extra_float_digits=3",
    )

    try:
        # Session poolers may override startup options; set these after connecting.
        conn.execute("SET TIME ZONE 'UTC'")
        conn.execute("SET extra_float_digits = 3")
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn
