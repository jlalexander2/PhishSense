"""Run integration tests only with an explicitly configured disposable test target."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from database import get_db_connection
import pytest
from validation_support import require_test_target

TABLES=('users','training_scenarios','training_sessions','training_responses','difficulty_evaluations')


def snapshot():
    with get_db_connection() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        result={}
        for table in TABLES:
            rows=conn.execute('SELECT * FROM public.'+table+' ORDER BY 1').fetchall()
            result[table]=dict(count=len(rows),digest=hashlib.sha256(
                json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest())
        return result


class SafeFailures:
    def pytest_runtest_logreport(self,report):
        if report.failed:
            text=str(report.longrepr).lower()
            print('Failure:',report.nodeid,'phase:',report.when,
                  'connection error:','operationalerror' in text,
                  'assertion:','assertionerror' in text)


def main():
    load_dotenv(ROOT/'.env')
    test_url=require_test_target()
    # Authentication is bound to the explicit project reference in the verified
    # pooler username/direct hostname. Do this before any schema-creating tests.
    with patch.dict(os.environ, {'DATABASE_URL':test_url}), get_db_connection() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        if not conn.pgconn.ssl_in_use or conn.execute('SELECT 1 AS ok').fetchone()['ok']!=1:
            raise RuntimeError('Disposable test connection could not be verified.')
    print('Distinct Supabase projects verified; disposable connection authenticated with verified TLS.', flush=True)
    if '--check-target' in sys.argv:
        print('Read-only target verification only; no tests or schema changes executed.')
        return 0
    baseline=snapshot()
    code=pytest.main(['-q','--tb=no','-x'],plugins=[SafeFailures()])
    unchanged=snapshot()==baseline
    print('Public production-table hashes unchanged:',unchanged)
    if code:return code
    with patch.dict(os.environ,{'DATABASE_URL':test_url}),get_db_connection() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        remaining=conn.execute("SELECT COUNT(*) AS n FROM information_schema.schemata WHERE schema_name LIKE 'phishsense_test_%'").fetchone()['n']
        print('Remaining test-target schemas:',remaining)
    return 0 if unchanged and remaining==0 else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print('Validation stopped. Error type:',type(error).__name__)
        print('Private details withheld. No automatic retry performed.')
        raise SystemExit(1)
