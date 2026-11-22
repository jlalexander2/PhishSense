from item_helpers import stored_plan, open_item, submit_item, reference
from datetime import datetime, timedelta, timezone
import secrets

import pytest
from psycopg.types.json import Jsonb

from performance import (measurements, summarize_session, historical_performance,
                         session_results, learner_history, complete_training_session)
from test_database import postgres
from test_control_schedule import application, register_client
from test_adaptive import seed


def row(i,correct=1,seconds=10,confidence=4,level='intermediate'):
    return dict(response_id=i,session_id=1,scenario_id=i,user_answer=1,is_correct=correct,
                response_time=seconds,confidence_level=confidence,difficulty_at_response=level,
                reasoning='Synthetic reasoning',subject='Synthetic',phishing_technique=None,learning_objectives=None)


def training(i=1,complete=True):
    now=datetime(2026,11,15,tzinfo=timezone.utc)+timedelta(days=i)
    return dict(session_id=i,started_at=now,completed_at=now if complete else None,
                study_group='experimental',scenario_ids=None,algorithm_version=None)


def test_exact_session_calculations_and_presented_difficulty():
    rows=[row(3,0,30,1,'advanced'),row(1,1,10,5),row(2,1,20,3)]
    s=summarize_session(training(),rows)
    assert s['response_count']==3 and s['correct_count']==2
    assert s['accuracy_percent']==pytest.approx(200/3)
    assert s['average_response_time']==20 and s['average_confidence']==3
    assert [r['response_id'] for r in s['responses']]==[1,2,3]
    assert s['responses'][-1]['expected_answer']==0
    easy,middle,hard=s['by_difficulty']
    assert easy['accuracy_percent'] is None and easy['response_count']==0
    assert middle['accuracy_percent']==100 and hard['accuracy_percent']==0
    assert s['practice_areas'][0]['error_type']=='false_alarm'
    assert s['confidence_distribution'][0]['count']==1


def test_empty_results_and_zero_time():
    m=measurements([])
    assert m['accuracy_percent'] is None and m['average_confidence'] is None
    assert m['average_response_time'] is None
    assert measurements([row(1,seconds=0)])['average_response_time']==0
    history=historical_performance([])
    assert history['completed_count']==0 and history['accuracy_change_points'] is None


def test_history_excludes_partial_and_weights_metrics_correctly():
    first=summarize_session(training(1),[row(1,0)])
    second=summarize_session(training(2),[row(i,1) for i in range(2,5)])
    partial=summarize_session(training(3,False),[row(i,0) for i in range(5,15)])
    history=historical_performance([partial,second,first])
    assert history['completed_count']==2
    assert history['overall']['accuracy_percent']==75  # Four responses, three correct.
    assert history['average_session_accuracy']==50  # Two sessions weighted equally.
    assert history['accuracy_change_points']==100
    assert len(history['in_progress'])==1
    assert [s['session_id'] for s in history['completed_sessions']]==[1,2]
    assert history['by_difficulty'][1]['response_count']==4


def populate(c,user,complete=False):
    ids=[r['scenario_id'] for r in c.execute('SELECT scenario_id FROM training_scenarios ORDER BY scenario_id LIMIT 10')]
    sid=c.execute("INSERT INTO training_sessions(user_id,session_type,scenario_ids,completed_at) VALUES (%s,'training',%s,CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END) RETURNING session_id",
                  (user,Jsonb(ids),complete)).fetchone()['session_id']
    return sid,ids


def answer(c,sid,scenario,correct=1):
    c.execute("INSERT INTO training_responses(session_id,scenario_id,user_answer,is_correct,reasoning,confidence_level,response_time,difficulty_at_response) VALUES (%s,%s,1,%s,'Synthetic reasoning',4,10,'intermediate')",(sid,scenario,correct))


def test_completion_atomic_idempotent_and_exact_plan(postgres):
    with postgres() as c:
        seed(c)
        user=c.execute("INSERT INTO users(username,email,password_hash) VALUES ('complete','complete@example.invalid','hash') RETURNING user_id").fetchone()['user_id']
        sid,ids=populate(c,user)
        for selected in ids[:9]:answer(c,sid,selected)
        assert not complete_training_session(c,user,sid)
        assert not complete_training_session(c,user+100,sid)
        answer(c,sid,ids[-1])
        assert complete_training_session(c,user,sid)
        stamp=c.execute('SELECT completed_at FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()['completed_at']
        assert complete_training_session(c,user,sid)
        assert c.execute('SELECT completed_at FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()['completed_at']==stamp
        # A duplicate cannot stand in for the tenth unique planned scenario.
        bad,ids=populate(c,user)
        for selected in ids[:9]:answer(c,bad,selected)
        answer(c,bad,ids[0])
        assert not complete_training_session(c,user,bad)
    # A rolled-back final response must roll back the completion marker as well.
    with pytest.raises(RuntimeError):
        with postgres() as c:
            rollback,ids=populate(c,user)
            for selected in ids:answer(c,rollback,selected)
            assert complete_training_session(c,user,rollback)
            raise RuntimeError('Synthetic rollback')
    with postgres() as c:
        assert c.execute('SELECT 1 FROM training_sessions WHERE session_id=%s',(rollback,)).fetchone() is None


def test_results_and_history_private_read_only_no_backfill(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    client=app.test_client()
    assert client.get('/results').status_code==302 and client.get('/history').status_code==302
    with postgres() as c:
        seed(c)
        a=c.execute("INSERT INTO users(username,email,password_hash) VALUES ('viewer','viewer@example.invalid','hash') RETURNING user_id").fetchone()['user_id']
        b=c.execute("INSERT INTO users(username,email,password_hash) VALUES ('other','other@example.invalid','hash') RETURNING user_id").fetchone()['user_id']
        sid,ids=populate(c,a,True)
        for selected in ids:answer(c,sid,selected)
        c.execute("UPDATE training_responses SET reasoning='<script>private</script>' WHERE session_id=%s",(sid,))
        partial,ids=populate(c,a)
        for selected in ids:answer(c,partial,selected)  # Legacy unmarked completion must remain untouched.
        other,ids=populate(c,b,True)
        answer(c,other,ids[0])
        tables=('users','training_sessions','training_responses','training_scenarios','difficulty_evaluations')
        before={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
    with client.session_transaction() as state:state['user_id']=a
    page=client.get('/results')
    assert page.status_code==200 and page.headers['Cache-Control']=='no-store'
    assert b'100.0%' in page.data and b'&lt;script&gt;private&lt;/script&gt;' in page.data
    assert b'<script>private</script>' not in page.data
    assert client.get('/results?session_id='+str(other)).status_code==404
    assert client.get('/results?session_id=invalid').status_code==400
    assert client.get('/results?session_id=-1').status_code==400
    assert b'still in progress' in client.get('/results?session_id='+str(partial)).data
    history=client.get('/history')
    assert history.status_code==200 and history.headers['Cache-Control']=='no-store'
    assert f'href="/results?session_id={other}"'.encode() not in history.data
    with postgres() as c:
        assert learner_history(c,a)['completed_count']==1
        assert session_results(c,a,other) is None
        assert before=={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}


def test_empty_views_and_start_action_security(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed(c)
    client=register_client(app,postgres,'fresh','experimental')
    assert b'Your results start here' in client.get('/results').data
    assert b'No completed sessions yet' in client.get('/history').data
    assert client.get('/training/start').status_code==405
    assert client.post('/training/start',data={'form_token':'wrong'}).status_code==400
    with client.session_transaction() as state:token=state['start_training_token']
    assert client.post('/training/start',data={'form_token':token}).status_code==302
    with client.session_transaction() as state:first=state['training_session_id']
    assert client.post('/training/start',data={'form_token':token}).status_code==302
    with client.session_transaction() as state:assert state['training_session_id']==first
    with postgres() as c:
        assert c.execute('SELECT COUNT(*) AS n FROM training_sessions').fetchone()['n']==1


def test_tenth_response_completes_before_inbox_and_allows_next_session(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed(c,hard=True)
    client=register_client(app,postgres,'finish','experimental')
    client.get('/inbox')
    with client.session_transaction() as state:sid=state['training_session_id']
    reviewed=set()
    for index in range(10):
        with client.session_transaction() as state:
            scenario=next(i for i in stored_plan(postgres,state) if i not in reviewed)
        assert open_item(client,scenario).status_code==200
        with client.session_transaction() as state:token=state['active_form_token']
        with postgres() as c:
            answer_value=c.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(scenario,)).fetchone()['is_phishing']
        feedback=submit_item(client,dict(scenario_id=scenario,user_answer=answer_value,
            confidence_level=5,reasoning='Synthetic milestone five response',form_token=token))
        assert feedback.status_code==200
        reviewed.add(scenario)
        with postgres() as c:
            complete=c.execute('SELECT completed_at FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()['completed_at']
        assert (complete is not None)==(index==9)
    assert b'View Session Results' in feedback.data
    result=client.get('/results?session_id='+str(sid))
    assert result.status_code==200 and b'100.0%' in result.data
    assert b'Hard' in result.data and b'Synthetic milestone five response' in result.data
    with postgres() as c:
        old_session=c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
        old_responses=c.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()
    with client.session_transaction() as state:start_token=state['start_training_token']
    assert client.post('/training/start',data={'form_token':start_token}).status_code==302
    with client.session_transaction() as state:
        assert state['training_session_id']!=sid
        assert len(stored_plan(postgres,state))==10
    with postgres() as c:
        assert c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()==old_session
        assert c.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()==old_responses
        assert c.execute('SELECT COUNT(*) AS n FROM training_sessions').fetchone()['n']==2


@pytest.mark.parametrize('mode',['empty','in_progress','completed'])
def test_results_and_history_templates_offline(monkeypatch,mode):
    import importlib
    from unittest.mock import MagicMock
    monkeypatch.setenv('PHISHSENSE_SECRET_KEY',secrets.token_hex(32))
    module=importlib.import_module('app')
    module.app.config['TESTING']=True
    conn=MagicMock()
    conn.execute.return_value.fetchone.return_value={'session_id':1}
    monkeypatch.setattr(module,'get_db_connection',lambda:conn)
    summary=None if mode=='empty' else summarize_session(training(1,mode=='completed'),
        [dict(row(1),reasoning='<script>synthetic</script>')])
    monkeypatch.setattr(module,'session_results',lambda *args:summary)
    monkeypatch.setattr(module,'learner_history',lambda *args:historical_performance([summary] if summary else []))
    client=module.app.test_client()
    with client.session_transaction() as state:state['user_id']=1
    result=client.get('/results');history=client.get('/history')
    assert result.status_code==history.status_code==200
    assert b'<script>synthetic</script>' not in result.data
    if mode=='completed':
        assert b'&lt;script&gt;synthetic&lt;/script&gt;' in result.data
        assert b'Performance by difficulty' in result.data
        assert b'Completed-session performance by difficulty' in history.data
    elif mode=='in_progress':
        assert b'still in progress' in result.data
        assert b'No completed sessions yet' in history.data
    else:
        assert b'Your results start here' in result.data
    assert result.headers['Cache-Control']==history.headers['Cache-Control']=='no-store'
