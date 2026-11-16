import pytest
from validation_support import require_test_target, supabase_project

A='a'*20
B='b'*20


def direct(ref):
    return f'postgresql://postgres@db.{ref}.supabase.co:5432/postgres'


def pooler(ref):
    return f'postgresql://postgres.{ref}@aws-0-us-east-1.pooler.supabase.com:5432/postgres'


def test_explicit_separate_project_required(monkeypatch):
    monkeypatch.setenv('DATABASE_URL',direct(A))
    monkeypatch.delenv('TEST_DATABASE_URL',raising=False)
    with pytest.raises(ValueError,match='required'):
        require_test_target()
    monkeypatch.setenv('TEST_DATABASE_URL',pooler(B))
    assert require_test_target()==pooler(B)


@pytest.mark.parametrize('target',[direct(A),pooler(A),pooler(A).replace(':5432/',':6543/')])
def test_same_project_cannot_bypass_guard_with_different_endpoints(monkeypatch,target):
    monkeypatch.setenv('DATABASE_URL',direct(A))
    monkeypatch.setenv('TEST_DATABASE_URL',target)
    with pytest.raises(ValueError,match='different Supabase project'):
        require_test_target()


@pytest.mark.parametrize('url',[
    'postgresql://test@localhost/postgres',
    direct(B)+'?hostaddr=127.0.0.1',
    'postgresql://postgres@aws-0-us-east-1.pooler.supabase.com:5432/postgres',
])
def test_unverifiable_targets_rejected(url):
    with pytest.raises(ValueError):
        supabase_project(url)
