"""Credential-safe disposable-only validation; no production connection or retry.

Usage: python scripts/validate_milestone6.py [pytest test paths/node IDs]
All tests run when no targets are given. Production hashes are not queried.
"""
import os,sys,socket,time,re
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import database,psycopg,pytest
from validation_support import require_test_target,supabase_project
from psycopg.conninfo import conninfo_to_dict

CATEGORIES=('connection refused','timeout expired','too many clients','remaining connection slots','password authentication failed','certificate verify failed','could not translate host name','server closed','connection reset')
def safe(e):return {'type':type(e).__name__,'sqlstate':getattr(e,'sqlstate',None),'categories':[v for v in CATEGORIES if v in str(e).lower()]}
class Evidence:
 def pytest_exception_interact(self,node,call,report):
  print('Safe failure:',node.nodeid,report.when,safe(call.excinfo.value),flush=True)
  print('Code locations:',[(Path(e.path).name,e.lineno+1,e.name) for e in call.excinfo.traceback[-5:]],flush=True)

def main():
 test=require_test_target();target=conninfo_to_dict(test);reference=supabase_project(test)
 addresses={x[4][0] for x in socket.getaddrinfo(target['host'],target.get('port','5432'),type=socket.SOCK_STREAM)}
 original=psycopg.connect
 def guarded(conninfo='',**kwargs):
  params=conninfo_to_dict(conninfo)
  assert supabase_project(conninfo)==reference,'Non-test database connection blocked'
  assert all(params.get(k,'5432' if k=='port' else '')==target.get(k,'5432' if k=='port' else '') for k in ('host','user','dbname','port')),'Test routing mismatch'
  assert not any(k in kwargs for k in ('host','hostaddr','user','dbname','port','service')),'Routing override blocked'
  return original(conninfo,**kwargs)
 with patch.object(psycopg,'connect',guarded):
  with patch.dict(os.environ,{'DATABASE_URL':test}),database.get_db_connection() as c:
   c.execute('SET TRANSACTION READ ONLY');assert c.pgconn.ssl_in_use
   prior={r['schema_name'] for r in c.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'phishsense_test_%'")}
   activity=c.execute("SELECT count(*) AS n FROM pg_stat_activity").fetchone()['n']
  print('Distinct disposable project authenticated with verified TLS; DNS addresses:',len(addresses),'PostgreSQL activity:',activity,flush=True)
  print('All real database connections are guarded to TEST only; production access is blocked.',flush=True)
  code=pytest.main(['-q','--tb=no','-x',*sys.argv[1:]],plugins=[Evidence()])
  with patch.dict(os.environ,{'DATABASE_URL':test}),database.get_db_connection() as c:
   c.execute('SET TRANSACTION READ ONLY')
   after={r['schema_name'] for r in c.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'phishsense_test_%'")}
  print('New automated schemas remaining:',len(after-prior),'existing namespaces preserved:',prior.issubset(after),flush=True)
  return int(code) if code else int(bool(after-prior) or not prior.issubset(after))
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:print('Validation stopped without retry:',safe(e),flush=True);raise SystemExit(1)
