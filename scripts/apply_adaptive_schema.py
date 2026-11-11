"""Apply the additive T14/T15 schema once, verifying historical fields unchanged."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from psycopg import sql
from database import get_db_connection

TABLES = ('users', 'training_scenarios', 'training_sessions', 'training_responses')


def apply():
    with get_db_connection() as conn:
        conn.execute('SET LOCAL search_path TO public')
        conn.execute("SET LOCAL lock_timeout = '5s'")
        conn.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE').format(
            sql.SQL(', ').join(map(sql.Identifier, TABLES))))
        if conn.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='study_group'").fetchone():
            raise ValueError('Adaptive schema already present; nothing applied')
        snapshots = {}
        for table in TABLES:
            rows = conn.execute(sql.SQL('SELECT * FROM {} ORDER BY 1').format(sql.Identifier(table))).fetchall()
            columns = [r['column_name'] for r in conn.execute('''SELECT column_name FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position''', (table,))]
            snapshots[table] = columns, rows
        migration = Path(__file__).resolve().parents[1] / 'migrations/004_adaptive_training.sql'
        conn.execute(migration.read_text())
        for table, (columns, before) in snapshots.items():
            after = conn.execute(sql.SQL('SELECT {} FROM {} ORDER BY 1').format(
                sql.SQL(', ').join(map(sql.Identifier, columns)), sql.Identifier(table))).fetchall()
            if before != after:
                raise ValueError('Historical field verification failed; transaction canceled')
            print(table + ': historical records verified unchanged; count=' + str(len(after)))
    print('Adaptive schema committed. Existing accounts remain unassigned; historical sessions are unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        print('Preview: adds study-group/session metadata and an RLS-enabled evaluation table. Use --apply only after approval.')
    else:
        try:
            apply()
        except Exception as error:
            print('Schema update stopped; transaction rolled back. Error type:', type(error).__name__)
            print('Details suppressed to protect credentials and personal data.')
            raise SystemExit(1)
