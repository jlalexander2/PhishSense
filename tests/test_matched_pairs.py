import hashlib
import json
from pathlib import Path
import time

from adaptive import (CONTROL_SCHEDULE, VERSION, ORDERED_VERSION, choose_schedule,
                      control_scenarios, pair_safe, select_scenarios, sequence_enforced)
from test_database import postgres
from test_adaptive import seed
from test_control_schedule import application, register_client, assert_cannot_skip
import pytest


def seed_pairs(conn):
    seed(conn)
    ids=[]
    for index in range(8):
        pair=f'synthetic-pair-{index % 3}' if index<6 else None
        row=conn.execute('''INSERT INTO training_scenarios
            (sender_name,sender_email,subject,email_body,is_phishing,difficulty_level,
             explanation,source_id,training_context,learning_objectives,matched_pair_id)
            VALUES ('Synthetic','test@example.invalid','Synthetic advanced','Context and email',
                    %s,'advanced','Synthetic explanation',%s,'Synthetic context',
                    '["Synthetic objective"]'::jsonb,%s) RETURNING scenario_id''',
                    (int(index<3 or index==6),f'synthetic-advanced-{index}',pair)).fetchone()
        ids.append(row['scenario_id'])
    conn.execute("UPDATE training_scenarios SET introduced_in_version=%s WHERE difficulty_level='advanced'", (VERSION,))
    return ids


def test_reviewed_sources_preserved():
    manifest=json.loads(Path('data/advanced_approval_manifest.json').read_text())
    for name,digest in manifest['source_sha256'].items():
        assert hashlib.sha256((Path('data')/name).read_bytes()).hexdigest()==digest
    approved=json.loads(Path('data/evercrest_advanced_approved.json').read_text())
    drafts=json.loads(Path('data/evercrest_advanced_scenarios_draft_v2.json').read_text())+json.loads(Path('data/evercrest_advanced_independent_drafts.json').read_text())
    for original,copy in zip(drafts,approved):
        for key in original:
            if key not in ('review_status','review_notes','matched_pair_id'):
                assert original[key]==copy[key]
        assert copy['review_status']=='approved'
    assert len(approved)==8
    assert all(r['matched_pair_id'] is None for r in approved[-2:])
    # Original JSONL lines remain byte-for-byte unchanged.
    lines=Path('data/scenarios_approved_for_prototype.jsonl').read_bytes().splitlines(keepends=True)
    assert hashlib.sha256(b''.join(lines[:-8])).hexdigest()==manifest['original_approved_jsonl_sha256']


def test_schedule_search_backtracks():
    pools={'intermediate':[{'scenario_id':1,'matched_pair_id':'pair'},
                           {'scenario_id':2,'matched_pair_id':None}],
           'advanced':[{'scenario_id':3,'matched_pair_id':'pair'}]}
    assert choose_schedule(pools,('intermediate','advanced'))==[2,3]
    assert choose_schedule(pools,('intermediate','advanced'),{'pair'}) is None
    assert sequence_enforced({'algorithm_version':ORDERED_VERSION})


def test_pair_selection_and_metadata_import(postgres,monkeypatch):
    import import_scenarios
    with postgres() as conn:
        ids=seed_pairs(conn)
        selected=select_scenarios(conn,0,'advanced',5)
        assert len(selected)==5 and pair_safe(conn,selected)
        assert set(ids[-2:]).issubset(selected)
        after_completed=select_scenarios(conn,0,'advanced',5,[ids[0]])
        assert ids[3] not in after_completed and ids[0] not in after_completed
        assert len(after_completed)==4
        assert len(control_scenarios(conn))==10
        assert pair_safe(conn,control_scenarios(conn))
        assert not pair_safe(conn,[ids[0],ids[3]])
        assert select_scenarios(conn,0,'advanced',5,pair_exclusion=False)==[]

    monkeypatch.setattr(import_scenarios,'get_db_connection',postgres)
    synthetic=dict(source_id='synthetic-import',sender_name='Test',sender_email='test@example.invalid',
        subject='Synthetic',email_body='Synthetic context and message',is_phishing=1,
        difficulty_level='advanced',explanation='Synthetic explanation',review_status='approved',
        training_context='Synthetic context',learning_objectives=['Objective'],matched_pair_id='synthetic-import-pair')
    assert import_scenarios.import_scenarios([synthetic])['inserted']==1
    assert import_scenarios.import_scenarios([synthetic])['skipped']==1
    with postgres() as conn:
        row=conn.execute('SELECT * FROM training_scenarios WHERE source_id=%s',('synthetic-import',)).fetchone()
        assert row['learning_objectives']==['Objective']
        assert row['training_context']=='Synthetic context'
        assert row['matched_pair_id']=='synthetic-import-pair'


@pytest.mark.parametrize('group',['experimental','control'])
def test_full_pair_aware_workflow(postgres,monkeypatch,group):
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        hard_ids=seed_pairs(conn)
    client=register_client(app,postgres,'paired',group)
    assert client.get('/inbox').status_code==200
    with client.session_transaction() as state:
        sid=state['training_session_id']
        initial=state['training_scenario_ids']
    assert_cannot_skip(client,postgres,sid,initial)
    reviewed=[]
    for index in range(10):
        client.get('/inbox')
        with client.session_transaction() as state:
            ids=state['training_scenario_ids']
        scenario_id=next(i for i in ids if i not in reviewed)
        assert client.get(f'/training?scenario_id={scenario_id}').status_code==200
        with client.session_transaction() as state:
            token=state['active_form_token']
            state['scenario_started_at']=time.time()-10
        with postgres() as conn:
            answer=conn.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(scenario_id,)).fetchone()['is_phishing']
        # Controls intentionally perform badly; the schedule must still apply.
        response=client.post('/training',data=dict(scenario_id=scenario_id,
            user_answer=answer if group=='experimental' else 1-answer,confidence_level=4,
            reasoning='Synthetic explanation',form_token=token))
        assert response.status_code==200
        reviewed.append(scenario_id)
        with postgres() as conn:
            session=conn.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
            assert session['algorithm_version']==VERSION
            assert len(session['scenario_ids'])==10
            assert pair_safe(conn,session['scenario_ids'])
            if index==4 and group=='experimental':
                assert session['current_difficulty']=='advanced'
                assert len(set(session['scenario_ids'][5:]))==5
                assert set(hard_ids[-2:]).issubset(session['scenario_ids'])
    assert b'Training Complete!' in client.get('/inbox').data
    with postgres() as conn:
        responses=conn.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()
        assert len(responses)==10
        expected=('intermediate',)*5+('advanced',)*5 if group=='experimental' else CONTROL_SCHEDULE
        assert tuple(r['difficulty_at_response'] for r in responses)==expected
        assert pair_safe(conn,[r['scenario_id'] for r in responses])
        assert session['study_group']==group
        assert all(r['reasoning']=='Synthetic explanation' for r in responses)


def test_pair_conflict_blocks_control_instead_of_shortening(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        ids=seed_pairs(conn)
        conn.execute('DELETE FROM training_scenarios WHERE difficulty_level=%s AND NOT (scenario_id=ANY(%s))',('advanced',[ids[0],ids[3]]))
    client=register_client(app,postgres,'conflict','control')
    assert client.get('/inbox').status_code==503
    with postgres() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM training_sessions').fetchone()['n']==0


def test_old_session_cannot_select_newly_introduced_content(postgres):
    from adaptive import evaluate_session
    from psycopg.types.json import Jsonb
    with postgres() as conn:
        seed_pairs(conn)
        user=conn.execute("INSERT INTO users(username,email,password_hash) VALUES ('old','old@example.invalid','hash') RETURNING user_id").fetchone()['user_id']
        ids=select_scenarios(conn,user,'intermediate',10)
        previous=conn.execute('''INSERT INTO training_sessions
            (user_id,session_type,study_group,algorithm_version,scenario_ids)
            VALUES (%s,'training','experimental',%s,%s) RETURNING *''',(user,ORDERED_VERSION,Jsonb(ids))).fetchone()
        for sid in ids[:5]:
            conn.execute('''INSERT INTO training_responses
                (session_id,scenario_id,user_answer,is_correct,confidence_level,response_time,difficulty_at_response)
                VALUES (%s,%s,1,1,5,10,'intermediate')''',(previous['session_id'],sid))
        assert evaluate_session(conn,previous)==ids
        current=conn.execute('SELECT * FROM training_sessions WHERE session_id=%s',(previous['session_id'],)).fetchone()
        assert current['algorithm_version']==ORDERED_VERSION
        assert current['current_difficulty']=='intermediate'
        assert current['scenario_ids']==ids


def test_server_rejects_conflicting_persisted_selection(postgres,monkeypatch):
    from psycopg.types.json import Jsonb
    app=application(postgres,monkeypatch)
    with postgres() as conn:
        hard=seed_pairs(conn)
    client=register_client(app,postgres,'invalid-selection','experimental')
    client.get('/inbox')
    with client.session_transaction() as state:
        ids=state['training_scenario_ids']
        sid=state['training_session_id']
    # Model inconsistent stored metadata; a signed browser cookie cannot bypass it.
    with postgres() as conn:
        invalid=ids[:8]+[hard[0],hard[3]]
        conn.execute('UPDATE training_sessions SET scenario_ids=%s WHERE session_id=%s',(Jsonb(invalid),sid))
    assert client.get(f'/training?scenario_id={ids[0]}').status_code==200
    with client.session_transaction() as state:
        token=state['active_form_token']
    response=client.post('/training',data=dict(scenario_id=ids[0],user_answer=1,
        confidence_level=4,reasoning='Synthetic',form_token=token))
    assert response.status_code==409
    with postgres() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM training_responses').fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) AS n FROM difficulty_evaluations').fetchone()['n']==0
