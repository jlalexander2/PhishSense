import secrets
import importlib

import pytest
from psycopg.types.json import Jsonb

from mistakes import summarize_mistakes, learner_mistakes
from test_database import postgres


def response(i, answer=0, correct=0, technique=None, objectives=None):
    return dict(response_id=i, user_answer=answer, is_correct=correct,
                phishing_technique=technique, learning_objectives=objectives)


@pytest.mark.parametrize('count',[0,1,2,3])
def test_recurrence_threshold(count):
    summary=summarize_mistakes([response(i) for i in range(count)])
    missed,alarm=summary['errors']
    assert missed['count']==count and missed['recurring']==(count>=2)
    assert alarm['count']==0 and not alarm['recurring']


def test_independent_error_types_correct_answers_and_duplicate_rows():
    rows=[response(1,0),response(2,1),response(3,0,1),response(4,1,1)]
    assert [r['count'] for r in summarize_mistakes(rows)['errors']]==[1,1]
    rows += [response(5,0),response(6,1),response(5,0)]
    summary=summarize_mistakes(rows)
    assert all(e['count']==2 and e['recurring'] for e in summary['errors'])


def test_exact_metadata_associations_and_no_invented_categories():
    rows=[response(1,technique='Exact stored technique',objectives=['Exact objective','Exact objective','']),
          response(2,technique='Exact stored technique',objectives=['Exact objective']),
          response(3,answer=1,objectives=['Exact objective']),
          response(4,technique=None,objectives=None),
          response(5,correct=1,technique='Must not appear',objectives=['Must not appear'])]
    summary=summarize_mistakes(rows)
    assert len(summary['associations'])==3
    assert {a['concept'] for a in summary['associations']}=={'Exact stored technique','Exact objective'}
    missed=[a for a in summary['associations'] if a['error_type']=='missed_phishing']
    assert all(a['count']==2 and a['recurring'] for a in missed)
    alarm=[a for a in summary['associations'] if a['error_type']=='false_alarm'][0]
    assert alarm['count']==1 and not alarm['recurring']
    assert summary['errors'][0]['count']==3  # Missing metadata still counts.


def add_user(conn,name,group):
    return conn.execute('INSERT INTO users(username,email,password_hash,study_group) VALUES (%s,%s,%s,%s) RETURNING user_id',
                        (name,name+'@example.invalid','synthetic-hash',group)).fetchone()['user_id']


def add_session(conn,user,group,kind='training'):
    return conn.execute('INSERT INTO training_sessions(user_id,session_type,study_group) VALUES (%s,%s,%s) RETURNING session_id',
                        (user,kind,group)).fetchone()['session_id']


def add_scenario(conn,truth,technique=None,objectives=None):
    return conn.execute('''INSERT INTO training_scenarios
        (sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,explanation,phishing_technique,learning_objectives)
        VALUES ('Synthetic','test@example.invalid','Synthetic','Body',%s,'intermediate','Explanation',%s,%s)
        RETURNING scenario_id''',(truth,technique,Jsonb(objectives) if objectives is not None else None)).fetchone()['scenario_id']


def add_answer(conn,sid,scenario,answer,correct):
    conn.execute('''INSERT INTO training_responses
        (session_id,scenario_id,user_answer,is_correct,reasoning,confidence_level,response_time,difficulty_at_response)
        VALUES (%s,%s,%s,%s,'Synthetic reasoning',4,10,'intermediate')''',(sid,scenario,answer,correct))


@pytest.mark.parametrize('group',['experimental','control'])
def test_learner_isolation_across_sessions_and_assessment_exclusion(postgres,group):
    with postgres() as c:
        first=add_user(c,'first',group); second=add_user(c,'second',group)
        phish=add_scenario(c,1,'Stored technique',['Stored objective'])
        legit=add_scenario(c,0)
        sid=add_session(c,first,group)
        add_answer(c,sid,phish,0,0)
        sid2=add_session(c,first,group)
        add_answer(c,sid2,phish,0,0)  # Same scenario in another session is a new occurrence.
        add_answer(c,sid2,legit,1,0)
        add_answer(c,sid2,legit,0,1)
        assessment=add_session(c,first,group,'pre_test')
        add_answer(c,assessment,legit,1,0)
        other=add_session(c,second,group)
        add_answer(c,other,legit,1,0)
        add_answer(c,other,phish,0,0)
        a=learner_mistakes(c,first); b=learner_mistakes(c,second)
        assert [e['count'] for e in a['errors']]==[2,1]
        assert [e['recurring'] for e in a['errors']]==[True,False]
        assert [e['count'] for e in b['errors']]==[1,1]
        assert all(not e['recurring'] for e in b['errors'])
        assert all(e['count']==0 for e in learner_mistakes(c,999999)['errors'])


def test_summary_route_is_read_only_authenticated_and_self_only(postgres,monkeypatch):
    monkeypatch.setenv('PHISHSENSE_SECRET_KEY',secrets.token_hex(32))
    module=importlib.import_module('app')
    monkeypatch.setattr(module,'get_db_connection',postgres)
    module.app.config['TESTING']=True
    client=module.app.test_client()
    assert client.get('/mistakes').status_code==302
    assert client.post('/mistakes').status_code==405
    with postgres() as c:
        first=add_user(c,'viewer','experimental'); other=add_user(c,'private','control')
        phish=add_scenario(c,1,'<script>unsafe</script>',['Visible objective'])
        hidden=add_scenario(c,1,'Other learner only',['Private objective'])
        sid=add_session(c,first,'experimental')
        add_answer(c,sid,phish,0,0); add_answer(c,sid,phish,0,0)
        private=add_session(c,other,'control')
        add_answer(c,private,hidden,0,0)
        tables=('users','training_sessions','training_responses','training_scenarios','difficulty_evaluations')
        before={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
    with client.session_transaction() as state:
        state['user_id']=first;state['username']='Synthetic viewer'
    for _ in range(2):
        page=client.get(f'/mistakes?user_id={other}')
        assert page.status_code==200 and page.headers['Cache-Control']=='no-store'
        assert b'Missed phishing' in page.data and b'False alarms' in page.data
        assert b'Recurring' in page.data and b'Visible objective' in page.data
        assert b'Other learner only' not in page.data and b'Private objective' not in page.data
        assert b'&lt;script&gt;unsafe&lt;/script&gt;' in page.data
        assert b'<script>unsafe</script>' not in page.data
    assert b'href="/mistakes"' in client.get('/dashboard').data
    with postgres() as c:
        assert before=={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
