import secrets
import importlib
import time

import pytest
from psycopg.types.json import Jsonb

from adaptive import VERSION, evaluate_difficulty, select_scenarios
from test_database import postgres


def block(correct, seconds=60, confidence=4):
    return [dict(is_correct=int(i < correct), response_time=seconds,
                 confidence_level=confidence) for i in range(5)]


@pytest.mark.parametrize('correct,seconds,confidence,expected', [
    (4,60,4,'advanced'), (5,60,4,'advanced'),
    (4,60.01,4,'intermediate'), (4,60,3.99,'intermediate'),
    (2,1,5,'beginner'), (0,100,1,'beginner'),
    (3,90,2,'intermediate'), (3,90.01,2,'beginner'),
    (3,91,2.01,'intermediate'), (3,10,5,'intermediate'),
    (5,100,1,'intermediate'),
])
def test_thresholds(correct, seconds, confidence, expected):
    assert evaluate_difficulty('intermediate', block(correct, seconds, confidence), 'experimental')[0] == expected


@pytest.mark.parametrize('group', ['control','unassigned'])
def test_nonadaptive_rules(group):
    for correct in (0,5):
        assert evaluate_difficulty('intermediate', block(correct), group) == ('intermediate','non_adaptive')


def test_bounds_and_complete_window():
    assert evaluate_difficulty('beginner', block(0), 'experimental')[0] == 'beginner'
    assert evaluate_difficulty('advanced', block(5), 'experimental')[0] == 'advanced'
    assert evaluate_difficulty('intermediate', block(5)[:4], 'experimental')[0] == 'intermediate'


def seed(conn, hard=False):
    for level, count in [('beginner',7),('intermediate',12),('advanced',7 if hard else 0)]:
        for i in range(count):
            conn.execute('''INSERT INTO training_scenarios
                (sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,explanation)
                VALUES ('Synthetic','test@example.invalid','Synthetic','Body',%s,%s,'Explanation')''', (i%2,level))


@pytest.mark.parametrize('group', ['experimental','unassigned'])
def test_adaptive_workflow(postgres, monkeypatch, group):
    monkeypatch.setenv('PHISHSENSE_SECRET_KEY',secrets.token_hex(32))
    application=importlib.import_module('app')
    monkeypatch.setattr(application,'get_db_connection',postgres)
    application.app.config['TESTING']=True
    with postgres() as conn:
        seed(conn)
    client=application.app.test_client()
    account=dict(username='test',email='test@example.invalid',password=secrets.token_urlsafe(24))
    client.post('/register',data=account)
    with postgres() as conn:
        conn.execute('UPDATE users SET study_group=%s',(group,))
    client.post('/login',data=account)
    client.get('/inbox')
    with client.session_transaction() as state:
        sid=state['training_session_id']
        initial=state['training_scenario_ids']
    with postgres() as conn:
        assert {r['difficulty_level'] for r in conn.execute('SELECT difficulty_level FROM training_scenarios WHERE scenario_id=ANY(%s)',(initial,))} == {'intermediate'}
    reviewed=[]
    for i in range(10):
        client.get('/inbox')
        with client.session_transaction() as state:
            ids=state['training_scenario_ids']
        scenario_id=next(s for s in ids if s not in reviewed)
        assert client.get(f'/training?scenario_id={scenario_id}').status_code == 200
        with client.session_transaction() as state:
            token=state['active_form_token']
            state['scenario_started_at']=time.time()-10
        with postgres() as conn:
            correct=conn.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(scenario_id,)).fetchone()['is_phishing']
        response=client.post('/training',data=dict(scenario_id=scenario_id,user_answer=1-correct if i<5 else correct,
                            confidence_level=4,reasoning='Synthetic reasoning',form_token=token))
        assert response.status_code==200
        reviewed.append(scenario_id)
        with postgres() as conn:
            current=conn.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
            decisions=conn.execute('SELECT * FROM difficulty_evaluations WHERE session_id=%s ORDER BY block_number',(sid,)).fetchall()
        assert len(decisions)==(i+1)//5
        if i == 1:
            # Assignment changes must not change treatment within an active session.
            with postgres() as conn:
                conn.execute("UPDATE users SET study_group=%s", ('control' if group == 'experimental' else 'experimental',))
            assert current['study_group'] == group
        if i==4:
            assert current['current_difficulty']==('beginner' if group=='experimental' else 'intermediate')
            assert set(reviewed).issubset(current['scenario_ids'])
            if group == 'experimental':
                stale = initial[5]
                assert client.get(f'/training?scenario_id={stale}').status_code == 302
                with client.session_transaction() as state:
                    state['training_scenario_ids'] = initial
                    state['active_scenario_id'] = stale
                    state['scenario_started_at'] = time.time()-10
                    state['active_form_token'] = 'stale-token'
                assert client.post('/training', data=dict(scenario_id=stale, user_answer=1,
                    confidence_level=4, reasoning='Stale submission', form_token='stale-token')).status_code == 400
                # Inbox membership is recovered from PostgreSQL, not stale cookies.
                client.get('/inbox')
                with client.session_transaction() as state:
                    assert state['training_scenario_ids'] == current['scenario_ids']
    assert b'Training Complete!' in client.get('/inbox').data
    with postgres() as conn:
        rows=conn.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()
        assert len(rows)==10
        assert {r['difficulty_at_response'] for r in rows[:5]}=={'intermediate'}
        assert {r['difficulty_at_response'] for r in rows[5:]}==({'beginner'} if group=='experimental' else {'intermediate'})
        assert len(set(decisions[0]['response_ids']) & set(decisions[1]['response_ids']))==0
        assert all(d['study_group']==group and d['algorithm_version']==VERSION for d in decisions)
        assert current['current_difficulty']=='intermediate'


@pytest.mark.parametrize('hard', [False,True])
def test_promotion_availability_and_selection(postgres, hard):
    from adaptive import evaluate_session
    with postgres() as conn:
        seed(conn,hard)
        user=conn.execute("INSERT INTO users(username,email,password_hash,study_group) VALUES ('synthetic','synthetic@example.invalid','hash','experimental') RETURNING user_id").fetchone()['user_id']
        ids=select_scenarios(conn,user,'intermediate',10)
        session=conn.execute('''INSERT INTO training_sessions
            (user_id,session_type,study_group,algorithm_version,scenario_ids)
            VALUES (%s,'training','experimental',%s,%s) RETURNING *''',(user,VERSION,Jsonb(ids))).fetchone()
        for scenario_id in ids[:5]:
            conn.execute('''INSERT INTO training_responses
                (session_id,scenario_id,user_answer,is_correct,confidence_level,response_time,difficulty_at_response)
                VALUES (%s,%s,1,1,4,60,'intermediate')''',(session['session_id'],scenario_id))
        new_ids=evaluate_session(conn,session)
        assert new_ids[:5]==ids[:5]
        decision=conn.execute('SELECT * FROM difficulty_evaluations').fetchone()
        assert decision['proposed_difficulty']=='advanced'
        assert decision['applied_difficulty']==('advanced' if hard else 'intermediate')
        if not hard:
            assert decision['reason']=='target_scenarios_unavailable'
        assert evaluate_session(conn,session) is None  # idempotent block
        for index, scenario_id in enumerate(ids[:5]):
            conn.execute("UPDATE training_responses SET answered_at='2020-01-01'::timestamptz + %s * INTERVAL '1 second' WHERE scenario_id=%s", (index, scenario_id))
        # Seven never-completed intermediate scenarios must precede any repeats.
        selected=select_scenarios(conn,user,'intermediate',12)
        assert set(selected[:7]).isdisjoint(ids[:5])
        assert selected[7:] == ids[:5]
        excluded=select_scenarios(conn,user,'intermediate',12,ids[:5])
        assert len(excluded)==7 and set(excluded).isdisjoint(ids[:5])


def test_legacy_sessions_are_not_evaluated(postgres):
    from adaptive import evaluate_session
    assert evaluate_session(None, {'algorithm_version':None}) is None
