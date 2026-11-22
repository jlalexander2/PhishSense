from item_helpers import stored_plan, open_item, submit_item, reference
"""T25–T30: synthetic-only functional and security verification."""
import importlib
import math
import secrets
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from werkzeug.datastructures import MultiDict

from security import database_id, tokens_match, valid_registration
from adaptive import VERSION, evaluate_session, select_scenarios
from performance import learner_history
from test_database import postgres, account_form
from test_adaptive import seed, block
from test_control_schedule import application, register_client
from test_performance import populate, answer


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setenv('PHISHSENSE_SECRET_KEY', secrets.token_hex(32))
    module = importlib.import_module('app')
    module.app.config['TESTING'] = True
    def forbidden():
        pytest.fail('Rejected input must not open a database connection')
    monkeypatch.setattr(module, 'get_db_connection', forbidden)
    return module, module.app.test_client()


def test_account_csrf_required_and_unicode_safe(offline):
    module, client = offline
    for path in ('/register', '/login', '/logout'):
        assert client.get(path).status_code == 200
        for token in ('', 'wrong', '☃'):
            response = client.post(path, data={'auth_form_token': token})
            assert response.status_code == 400
    with client.session_transaction() as state:
        state['user_id'] = 1
    assert client.get('/logout').status_code == 200  # GET cannot log a learner out.
    with client.session_transaction() as state:
        assert state['user_id'] == 1
    assert account_form(client, '/logout').status_code == 302
    with client.session_transaction() as state:
        assert 'user_id' not in state


def test_input_limits_and_ambiguous_fields_before_connection(offline):
    _, client = offline
    valid = dict(username='synthetic', email='synthetic@example.invalid', password=secrets.token_urlsafe(24))
    for patch in ({'username': ''}, {'username': 'x'*81}, {'username': 'a\x00b'},
                  {'email': 'invalid'}, {'email': 'x'*255}, {'password': ''},
                  {'password': 'x'*1025}, {'password': 'a\x00b'}):
        assert account_form(client, '/register', {**valid, **patch}).status_code == 400
    for patch in ({'email': ''}, {'email': 'x'*255}, {'password': 'x'*1025}, {'email': 'a\x00b'}):
        assert account_form(client, '/login', {**valid, **patch}).status_code == 400
    client.get('/login')
    with client.session_transaction() as state:
        token = state['auth_form_token']
    response = client.post('/login', data=MultiDict([
        ('email', 'a@example.invalid'), ('email', 'b@example.invalid'),
        ('password', valid['password']), ('auth_form_token', token)]))
    assert response.status_code == 400
    assert client.post('/login', data={'email': 'x'*70000}).status_code == 413


@pytest.mark.parametrize('path', ['/dashboard', '/inbox', '/training', '/results', '/history', '/mistakes'])
def test_protected_routes_reject_unsigned_and_tampered_cookie(offline, path):
    module, client = offline
    assert client.get(path).status_code == 302
    client.set_cookie(module.app.config['SESSION_COOKIE_NAME'], 'tampered.signature.value')
    response = client.get(path)
    assert response.status_code == 302 and response.location.endswith('/login')


def test_security_headers_and_cookie_flags(offline):
    _, client = offline
    response = client.get('/login')
    policy = response.headers['Content-Security-Policy']
    for rule in ("script-src 'none'", "object-src 'none'", "frame-src 'none'",
                 "form-action 'self'", "base-uri 'none'", "frame-ancestors 'none'"):
        assert rule in policy
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    cookie = response.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie


def test_identifier_and_token_validation():
    for value in ('not-a-number', '-1', '0', '2147483648', '9'*5000, None):
        assert database_id(value) is None
    assert database_id('2147483647') == 2147483647
    assert not tokens_match('☃', 'ascii-token')
    assert not tokens_match(None, 'token')
    assert tokens_match('same', 'same')
    assert valid_registration('Learner', 'learner@example.invalid', 'existing password')


def test_results_large_id_rejected_before_database(offline):
    _, client = offline
    with client.session_transaction() as state:
        state['user_id'] = 1
    for value in ('2147483648', '9'*5000):
        assert client.get('/results?session_id='+value).status_code == 400


@pytest.mark.parametrize('started', [float('nan'), float('inf'), float('-inf'), True, None])
def test_invalid_timing_cannot_enter_research_metrics(offline, started):
    _, client = offline
    with client.session_transaction() as state:
        state.update(user_id=1, training_session_id=1, training_nonce='fixture-nonce',
                     active_form_token='token', scenario_started_at=started)
        state['active_item_ref']=reference(client,1,state)
    response = submit_item(client,dict(scenario_id=1, user_answer=1,
        confidence_level=4, reasoning='Synthetic reasoning', form_token='token'))
    assert response.status_code == 400


def test_training_invalid_inputs_rejected_before_database(offline):
    _, client = offline
    with client.session_transaction() as state:
        state.update(user_id=1, training_session_id=1, training_nonce='fixture-nonce',
                     active_form_token='token', scenario_started_at=1)
        state['active_item_ref']=reference(client,1,state)
    payload = dict(scenario_id=1, user_answer=1, confidence_level=4,
                   reasoning='Synthetic reasoning', form_token='token')
    for patch in ({'reasoning': 'a\x00b'}, {'reasoning': ' '}, {'reasoning': 'x'*5001},
                  {'scenario_id': '2147483648'}, {'scenario_id': '1 OR 1=1'},
                  {'user_answer': 'true'}, {'confidence_level': '3.5'}, {'form_token': '☃'}):
        assert submit_item(client,{**payload, **patch}).status_code == 400


def test_dashboard_own_completed_metrics_and_no_writes(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    with postgres() as c:
        seed(c)
    client = register_client(app, postgres, 'dashboard', 'experimental')
    with postgres() as c:
        users = c.execute('SELECT user_id FROM users').fetchone()['user_id']
        first, ids = populate(c, users, True)
        for i in ids: answer(c, first, i)
        second, ids = populate(c, users, True)
        for i in ids: answer(c, second, i, 0)
        partial, ids = populate(c, users)
        answer(c, partial, ids[0], 0)
        other = c.execute("INSERT INTO users(username,email,password_hash) VALUES ('private','private@example.invalid','hash') RETURNING user_id").fetchone()['user_id']
        foreign, ids = populate(c, other, True)
        for i in ids: answer(c, foreign, i)
        tables = ('users','training_scenarios','training_sessions','training_responses','difficulty_evaluations')
        before = {t: c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
        summary = learner_history(c, users)
    page = client.get('/dashboard')
    assert page.status_code == 200
    assert b'50.0%' in page.data and b'20' in page.data
    assert b'-100.0 percentage points' in page.data
    assert b'1 in-progress session(s)' in page.data
    assert f'/results?session_id={second}'.encode() in page.data
    assert f'/results?session_id={foreign}'.encode() not in page.data
    assert summary['completed_count'] == 2
    assert summary['overall']['response_count'] == 20
    with postgres() as c:
        assert before == {t: c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}


def test_dashboard_empty_state_no_invented_score(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    client = register_client(app, postgres, 'empty-dashboard', 'control')
    page = client.get('/dashboard')
    assert b'No completed sessions yet' in page.data
    assert b'0.0%' not in page.data and b'100.0%' not in page.data


def test_unsafe_email_and_reasoning_remain_inert(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    attack = '<script>alert(1)</script><img src="https://external.example/pixel" onerror="alert(2)"><iframe src="https://external.example"></iframe><a href="javascript:alert(3)">open</a>'
    with postgres() as c:
        seed(c)
        c.execute('UPDATE training_scenarios SET sender_name=%s,subject=%s,email_body=%s,explanation=%s,training_context=%s',
                  (attack, attack, attack, attack, attack))
    client = register_client(app, postgres, 'unsafe', 'experimental')
    inbox = client.get('/inbox')
    with client.session_transaction() as state:
        scenario_id = stored_plan(postgres,state)[0]
        sid = state['training_session_id']
    page = open_item(client,scenario_id)
    with client.session_transaction() as state: token = state['active_form_token']
    with postgres() as c:
        correct = c.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(scenario_id,)).fetchone()['is_phishing']
    feedback = submit_item(client,dict(scenario_id=scenario_id, user_answer=correct,
        confidence_level=4, reasoning=attack, form_token=token))
    for response in (inbox, page, feedback):
        assert response.status_code == 200
        assert b'<script>' not in response.data and b'<img src=' not in response.data
        assert b'<iframe' not in response.data and b'href="javascript:' not in response.data
        assert b'&lt;script&gt;' in response.data
        assert "script-src 'none'" in response.headers['Content-Security-Policy']
    with postgres() as c:
        row = c.execute('SELECT * FROM training_responses WHERE session_id=%s',(sid,)).fetchone()
        assert row['reasoning'] == attack and row['is_correct'] == 1
        assert math.isfinite(row['response_time']) and row['response_time'] >= 0


def test_login_parameterization_session_rotation_and_logout(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    client = app.test_client()
    account = dict(username='auth', email='auth@example.invalid', password=secrets.token_urlsafe(24))
    assert b'Successful' in account_form(client, '/register', account).data
    for email in ("' OR 1=1 --", 'absent@example.invalid'):
        assert b'Invalid email or password' in account_form(client, '/login', {**account, 'email': email}).data
        with client.session_transaction() as state: assert 'user_id' not in state
    with client.session_transaction() as state:
        state['training_session_id'] = 999
        old_token = state['auth_form_token']
    assert account_form(client, '/login', account).status_code == 302
    with client.session_transaction() as state:
        assert 'training_session_id' not in state and 'auth_form_token' not in state
        assert 'user_id' in state
    assert client.get('/logout').status_code == 200
    assert client.post('/logout', data={'auth_form_token':old_token}).status_code == 400
    assert account_form(client, '/logout').status_code == 302
    for path in ('/dashboard','/inbox','/results','/history','/mistakes'):
        assert client.get(path).status_code == 302


def test_cross_learner_training_cookie_cannot_read_or_write(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    with postgres() as c: seed(c, hard=True)
    first = register_client(app, postgres, 'owner', 'experimental')
    first.get('/inbox')
    with first.session_transaction() as state:
        foreign_id = state['training_session_id']
        foreign_scenarios = stored_plan(postgres,state)
    second = register_client(app, postgres, 'intruder', 'control')
    # Even a correctly signed but stale/wrong-owner session reference fails ownership.
    with second.session_transaction() as state:
        state.update(training_session_id=foreign_id, training_scenario_ids=foreign_scenarios,
                     training_nonce='fixture-nonce', active_form_token='token', scenario_started_at=1)
        state['active_item_ref']=reference(second,foreign_scenarios[0],state)
    assert open_item(second,foreign_scenarios[0]).status_code == 302
    assert submit_item(second,dict(scenario_id=foreign_scenarios[0],user_answer=1,
        confidence_level=4,reasoning='Synthetic isolation check',form_token='token')).status_code == 400
    assert second.get('/results?session_id='+str(foreign_id)).status_code == 404
    with postgres() as c:
        assert c.execute('SELECT COUNT(*) AS n FROM training_responses').fetchone()['n'] == 0
        assert c.execute('SELECT COUNT(*) AS n FROM difficulty_evaluations').fetchone()['n'] == 0
        assert c.execute('SELECT completed_at FROM training_sessions WHERE session_id=%s',(foreign_id,)).fetchone()['completed_at'] is None


def test_partial_block_has_no_decision_and_short_target_keeps_plan(postgres, monkeypatch):
    from psycopg.types.json import Jsonb
    with postgres() as c:
        seed(c,hard=False)
        # Four hard scenarios cannot fill the five remaining positions.
        for i in range(4):
            c.execute("INSERT INTO training_scenarios(sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,explanation) VALUES ('Synthetic','test@example.invalid','Synthetic hard','Body',1,'advanced','Explanation')")
        uid = c.execute("INSERT INTO users(username,email,password_hash,study_group) VALUES ('fallback','fallback@example.invalid','hash','experimental') RETURNING user_id").fetchone()['user_id']
        ids = select_scenarios(c, uid, 'intermediate', 10)
        training = c.execute("INSERT INTO training_sessions(user_id,session_type,study_group,algorithm_version,scenario_ids) VALUES (%s,'training','experimental',%s,%s) RETURNING *",(uid, 'rules-v3-pair-exclusion', Jsonb(ids))).fetchone()
        for i in ids[:4]: answer(c, training['session_id'], i)
        assert evaluate_session(c, training) is None
        assert c.execute('SELECT COUNT(*) AS n FROM difficulty_evaluations').fetchone()['n'] == 0
        answer(c, training['session_id'], ids[4])
        assert evaluate_session(c, training) == ids
        decision = c.execute('SELECT * FROM difficulty_evaluations').fetchone()
        assert decision['reason'] == 'target_scenarios_unavailable'
        assert decision['proposed_difficulty'] == 'advanced'
        assert decision['applied_difficulty'] == 'intermediate'
        assert len(ids) == 10 and len(set(ids)) == 10
        assert evaluate_session(c, training) is None


def test_too_small_baseline_cannot_create_partial_session(postgres, monkeypatch):
    app = application(postgres, monkeypatch)
    with postgres() as c:
        seed(c)
        c.execute('DELETE FROM training_scenarios WHERE scenario_id IN (SELECT scenario_id FROM training_scenarios WHERE difficulty_level=\'intermediate\' ORDER BY scenario_id LIMIT 3)')
    client = register_client(app, postgres, 'short-baseline', 'experimental')
    assert client.get('/inbox').status_code == 503
    with postgres() as c:
        assert c.execute('SELECT COUNT(*) AS n FROM training_sessions').fetchone()['n'] == 0
