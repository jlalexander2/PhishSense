import secrets
import importlib
import time

import pytest

from adaptive import (CONTROL_SCHEDULE, LEGACY_VERSION, VERSION,
                      next_scenario, sequence_enforced)
from test_database import postgres
from test_adaptive import seed


def test_schedule_and_versioning():
    assert CONTROL_SCHEDULE == ('intermediate',)*5 + (
        'beginner','advanced','intermediate','beginner','advanced')
    assert sequence_enforced({'algorithm_version': VERSION})
    assert not sequence_enforced({'algorithm_version': LEGACY_VERSION})
    assert not sequence_enforced({'algorithm_version': None})
    assert next_scenario({'scenario_ids':[1,2,3]}, {1}) == 2
    assert next_scenario({'scenario_ids':[1,2,3]}, {1,2,3}) is None


def application(postgres, monkeypatch):
    monkeypatch.setenv('PHISHSENSE_SECRET_KEY',secrets.token_hex(32))
    module=importlib.import_module('app')
    monkeypatch.setattr(module,'get_db_connection',postgres)
    module.app.config['TESTING']=True
    return module.app


def register_client(app, postgres, name, group):
    client=app.test_client()
    account=dict(username=name,email=f'{name}@example.invalid',password=secrets.token_urlsafe(24))
    client.post('/register',data=account)
    with postgres() as conn:
        conn.execute('UPDATE users SET study_group=%s WHERE username=%s',(group,name))
    client.post('/login',data=account)
    return client


@pytest.mark.parametrize('hard_count',[0,1])
def test_control_unavailable_is_blocked(postgres,monkeypatch,hard_count):
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        seed(conn)
        for i in range(hard_count):
            conn.execute("INSERT INTO training_scenarios(sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,explanation) VALUES ('Test','test@example.invalid','Test','Body',1,'advanced','Explanation')")
    client=register_client(app,postgres,'control','control')
    page=client.get('/inbox')
    assert page.status_code==503
    assert b'Evercrest Group' in page.data
    assert b'Scheduled training is not available yet' in page.data
    with client.session_transaction() as state:
        assert 'training_session_id' not in state
    with postgres() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM training_sessions').fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) AS n FROM training_responses').fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) AS n FROM difficulty_evaluations').fetchone()['n']==0


def assert_cannot_skip(client,postgres,sid,ids):
    assert client.get(f'/training?scenario_id={ids[1]}').status_code==302
    # Simulate an old tab/forged submission with an otherwise valid session token.
    with client.session_transaction() as state:
        state['active_scenario_id']=ids[1]
        state['active_form_token']='valid-test-token'
        state['scenario_started_at']=time.time()-5
    rejected=client.post('/training',data=dict(scenario_id=ids[1],user_answer=1,
                         confidence_level=4,reasoning='Attempt to skip',form_token='valid-test-token'))
    assert rejected.status_code==400
    assert b'next available email' in rejected.data
    with postgres() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM training_responses WHERE session_id=%s',(sid,)).fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) AS n FROM difficulty_evaluations WHERE session_id=%s',(sid,)).fetchone()['n']==0


@pytest.mark.parametrize('group',['experimental','control'])
def test_sequence_enforcement_and_inbox(postgres,monkeypatch,group):
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        seed(conn,hard=True)
    client=register_client(app,postgres,'sequence',group)
    page=client.get('/inbox')
    with client.session_transaction() as state:
        ids=state['training_scenario_ids']
        sid=state['training_session_id']
    assert b'Evercrest Group' in page.data
    assert page.data.count(b'class="email-row locked"')==9
    assert f'href="/training?scenario_id={ids[0]}"'.encode() in page.data
    assert f'href="/training?scenario_id={ids[1]}"'.encode() not in page.data
    assert_cannot_skip(client,postgres,sid,ids)


def test_fixed_control_sequence_ignores_all_performance(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        seed(conn,hard=True)  # Synthetic data only in the temporary test schema.
    sequences=[]
    for name,correct,seconds,confidence in [('strong',True,1,5),('struggling',False,180,1)]:
        client=register_client(app,postgres,name,'control')
        assert client.get('/inbox').status_code==200
        with client.session_transaction() as state:
            ids=state['training_scenario_ids']
            sid=state['training_session_id']
        sequences.append(ids)
        for index,scenario_id in enumerate(ids):
            assert client.get(f'/training?scenario_id={scenario_id}').status_code==200
            with client.session_transaction() as state:
                token=state['active_form_token']
                state['scenario_started_at']=time.time()-seconds
            with postgres() as conn:
                answer=conn.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(scenario_id,)).fetchone()['is_phishing']
            result=client.post('/training',data=dict(scenario_id=scenario_id,user_answer=answer if correct else 1-answer,
                               confidence_level=confidence,reasoning='Synthetic research reasoning',form_token=token))
            assert result.status_code==200
            page=client.get('/inbox')
            assert f'{index+1} of 10 Emails Reviewed'.encode() in page.data
            with postgres() as conn:
                current=conn.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
                assert current['scenario_ids']==ids
                assert current['current_difficulty']==CONTROL_SCHEDULE[min(index+1,9)]
        assert b'Training Complete!' in page.data
        with postgres() as conn:
            responses=conn.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()
            assert tuple(r['difficulty_at_response'] for r in responses)==CONTROL_SCHEDULE
            assert all(r['is_correct']==int(correct) and r['confidence_level']==confidence for r in responses)
            assert all(r['reasoning']=='Synthetic research reasoning' and r['response_time']>=seconds for r in responses)
            decisions=conn.execute('SELECT * FROM difficulty_evaluations WHERE session_id=%s ORDER BY block_number',(sid,)).fetchall()
            assert len(decisions)==2
            assert all(d['reason']=='fixed_control_schedule' for d in decisions)
            assert all(d['accuracy']==int(correct) for d in decisions)
    assert sequences[0]==sequences[1]
