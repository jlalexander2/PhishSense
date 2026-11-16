"""Fail-closed selection of an explicitly separate disposable Supabase project."""
import os
import re
from psycopg.conninfo import conninfo_to_dict


def supabase_project(url):
    params=conninfo_to_dict(url)
    host=params.get('host','').lower()
    if params.get('hostaddr') or params.get('service') or ',' in host:
        raise ValueError('An explicit Supabase hostname without routing overrides is required.')
    match=re.fullmatch(r'db\.([a-z0-9]{20})\.supabase\.co',host)
    if match:
        return match.group(1)
    if host.endswith('.pooler.supabase.com'):
        reference=params.get('user','').rsplit('.',1)[-1]
        if re.fullmatch(r'[a-z0-9]{20}',reference):
            return reference
    raise ValueError('Cannot verify the Supabase project identity from this connection.')


def require_test_target():
    test_url=os.environ.get('TEST_DATABASE_URL')
    production_url=os.environ.get('DATABASE_URL')
    if not test_url:
        raise ValueError('TEST_DATABASE_URL is required; production fallback is forbidden.')
    if not production_url:
        raise ValueError('DATABASE_URL is required for the read-only project separation check.')
    if supabase_project(test_url)==supabase_project(production_url):
        raise ValueError('Tests must use a different Supabase project from production.')
    return test_url
