"""Approved v4 quotas; old protocols and all participant outcomes stay unchanged."""
import copy
import time
from collections import Counter

import pytest
from psycopg.types.json import Jsonb

from adaptive import (VERSION, PAIR_VERSION, ORDERED_VERSION, LEGACY_VERSION,
    LEVELS, CONTROL_SCHEDULE, balanced_session_scenarios, balanced_candidates,
    choose_balanced_schedule, balanced_plan_safe, sequence_enforced, evaluate_session,
    ControlScheduleUnavailable)
from scenario_review import load_review, seed_review
from test_scenario_review import original_rows
from test_database import postgres, account_form
from test_control_schedule import application, register_client
from item_helpers import stored_plan, open_item, submit_item


def pools():
    data={level:[] for level in LEVELS}
    for sid,item in enumerate(load_review().values(),1):
        s=item['proposed']
        data[s['difficulty_level']].append(dict(scenario_id=sid,
            is_phishing=s['is_phishing'],difficulty_level=s['difficulty_level'],
            matched_pair_id=s.get('matched_pair_id')))
    return data


def assert_plan(plan,data,schedule):
    lookup={r['scenario_id']:r for pool in data.values() for r in pool}
    selected=[lookup[i] for i in plan]
    assert len(plan)==len(set(plan))==10
    assert sum(r['is_phishing'] for r in selected)==5
    assert sum(r['is_phishing'] for r in selected[:5])==2
    assert sum(r['is_phishing'] for r in selected[5:])==3
    assert tuple(r['difficulty_level'] for r in selected)==tuple(schedule)
    pairs=[r['matched_pair_id'] for r in selected if r['matched_pair_id']]
    assert len(pairs)==len(set(pairs))


@pytest.mark.parametrize('target',LEVELS)
def test_real_inventory_all_three_adaptive_paths(target):
    data=pools();before=copy.deepcopy(data)
    initial=choose_balanced_schedule(data,('intermediate',)*10,require_branches=True)
    assert_plan(initial,data,('intermediate',)*10)
    lookup={r['scenario_id']:r for pool in data.values() for r in pool}
    prefix=[lookup[i] for i in initial[:5]]
    schedule=('intermediate',)*5+(target,)*5
    plan=choose_balanced_schedule(data,schedule,prefix)
    assert plan[:5]==initial[:5]
    assert_plan(plan,data,schedule)
    if target=='advanced':
        independent={r['scenario_id'] for r in data[target] if not r['matched_pair_id']}
        assert independent.issubset(plan)
    assert data==before


def test_control_is_deterministic_and_not_performance_dependent():
    data=pools()
    plan=choose_balanced_schedule(data,CONTROL_SCHEDULE)
    for _ in range(3):assert choose_balanced_schedule(data,CONTROL_SCHEDULE)==plan
    assert_plan(plan,data,CONTROL_SCHEDULE)


@pytest.mark.parametrize('level',LEVELS)
def test_creation_blocks_if_any_experimental_branch_is_infeasible(level):
    data=pools();data[level]=[r for r in data[level] if not r['is_phishing']]
    assert choose_balanced_schedule(data,('intermediate',)*10,require_branches=True) is None


def test_no_pair_relaxation_or_baseline_quota_relaxation():
    data=pools();hard=data['advanced']
    # Preserve adequate raw count but leave fewer than five independent pair choices.
    for r in hard:r['matched_pair_id']='one-shared-pair'
    assert choose_balanced_schedule(data,('intermediate',)*10,require_branches=True) is None
    data=pools();prefix=[r for r in data['intermediate'] if r['is_phishing']][:5]
    assert choose_balanced_schedule(data,('intermediate',)*10,prefix) is None


def test_legacy_protocols_remain_distinguishable_and_ordered():
    assert VERSION=='rules-v4-balanced-selection' and PAIR_VERSION=='rules-v3-pair-exclusion'
    assert all(sequence_enforced({'algorithm_version':v}) for v in (ORDERED_VERSION,PAIR_VERSION,VERSION))
    assert not sequence_enforced({'algorithm_version':LEGACY_VERSION})


@pytest.mark.parametrize('group,outcome,target',[
    ('experimental','poor','beginner'),('experimental','maintain','intermediate'),
    ('experimental','strong','advanced'),('control','poor',None),('control','strong',None)])
def test_balanced_full_workflow(postgres,monkeypatch,group,outcome,target):
    app=application(postgres,monkeypatch)
    with postgres() as c:assert seed_review(c,original_rows())==27
    client=register_client(app,postgres,'balanced',group)
    assert client.get('/inbox').status_code==200
    with client.session_transaction() as state:
        sid=state['training_session_id'];initial=stored_plan(postgres,state)
    with postgres() as c:
        assert balanced_plan_safe(c,initial)
        tables=('training_scenarios','users')
        before={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
    for index in range(10):
        with client.session_transaction() as state:plan=stored_plan(postgres,state)
        item=plan[index]
        page=open_item(client,item);assert page.status_code==200
        assert b'rules-v4' not in page.data and b'is_phishing' not in page.data
        assert b'classification quota' not in page.data.lower()
        with client.session_transaction() as state:
            token=state['active_form_token'];state['scenario_started_at']=time.time()-10
        with postgres() as c:truth=c.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=%s',(item,)).fetchone()['is_phishing']
        correct=outcome=='strong' or (outcome=='maintain' and index<3)
        response=submit_item(client,dict(scenario_id=item,user_answer=truth if correct else 1-truth,
            confidence_level=4,reasoning='Synthetic balanced workflow reasoning',form_token=token))
        assert response.status_code==200
        if index==4:
            with postgres() as c:
                training=c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
                decision=c.execute('SELECT * FROM difficulty_evaluations WHERE session_id=%s',(sid,)).fetchone()
                assert training['algorithm_version']==VERSION
                assert balanced_plan_safe(c,training['scenario_ids'])
                if group=='control':assert training['scenario_ids']==initial and decision['reason']=='fixed_control_schedule'
                else:assert decision['applied_difficulty']==target
    with postgres() as c:
        training=c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()
        rows=c.execute('''SELECT r.*,s.is_phishing FROM training_responses r
            JOIN training_scenarios s USING(scenario_id) WHERE session_id=%s ORDER BY response_id''',(sid,)).fetchall()
        assert training['completed_at'] is not None and len(rows)==10
        assert sum(r['is_phishing'] for r in rows)==5
        assert sum(r['is_phishing'] for r in rows[:5])==2
        schedule=CONTROL_SCHEDULE if group=='control' else ('intermediate',)*5+(target,)*5
        assert tuple(r['difficulty_at_response'] for r in rows)==schedule
        assert all(r['is_correct']==int(r['user_answer']==r['is_phishing']) for r in rows)
        assert all(r['confidence_level']==4 and r['response_time']>=0 and r['reasoning']=='Synthetic balanced workflow reasoning' for r in rows)
        assert before=={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
    assert client.get('/results?session_id='+str(sid)).status_code==200


@pytest.mark.parametrize('version',[LEGACY_VERSION,ORDERED_VERSION,PAIR_VERSION])
def test_old_sessions_resume_without_rebalancing_or_historical_edits(postgres,monkeypatch,version):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed_review(c,original_rows())
    old=register_client(app,postgres,'legacy-balance','experimental')
    with postgres() as c:
        uid=c.execute("SELECT user_id FROM users WHERE username='legacy-balance'").fetchone()['user_id']
        ids=[r['scenario_id'] for r in c.execute("SELECT scenario_id FROM training_scenarios WHERE difficulty_level='intermediate' ORDER BY is_phishing DESC,scenario_id LIMIT 10")]
        saved=c.execute("""INSERT INTO training_sessions(user_id,session_type,study_group,algorithm_version,scenario_ids)
            VALUES (%s,'training','experimental',%s,%s) RETURNING *""",(uid,version,Jsonb(ids))).fetchone()
        # All-phishing baseline is intentionally historical and must remain unaltered.
        assert sum(r['is_phishing'] for r in c.execute('SELECT is_phishing FROM training_scenarios WHERE scenario_id=ANY(%s)',(ids[:5],)))==5
    with postgres() as c:
        c.execute("""INSERT INTO training_responses(session_id,scenario_id,user_answer,is_correct,reasoning,confidence_level,response_time,difficulty_at_response)
            SELECT %s,scenario_id,is_phishing,1,'Preserved historical reasoning',3,17,'intermediate'
            FROM training_scenarios WHERE scenario_id=%s""",(saved['session_id'],ids[0]))
    old.get('/dashboard')
    with old.session_transaction() as state:token=state['start_training_token']
    assert old.post('/training/start',data={'form_token':token}).status_code==302
    with old.session_transaction() as state:assert state['training_session_id']==saved['session_id']
    assert old.get('/inbox').status_code==200
    with postgres() as c:
        assert c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(saved['session_id'],)).fetchone()==saved
        old_tables={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in ('training_responses','difficulty_evaluations')}
    fresh=register_client(app,postgres,'new-balance','experimental')
    assert fresh.get('/inbox').status_code==200
    with postgres() as c:
        assert c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(saved['session_id'],)).fetchone()==saved
        assert old_tables=={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in old_tables}
        new=c.execute("SELECT * FROM training_sessions WHERE user_id<>%s",(uid,)).fetchone()
        assert new['algorithm_version']==VERSION and balanced_plan_safe(c,new['scenario_ids'])


def test_new_protocol_inventory_loss_preserves_balanced_fallback(postgres):
    with postgres() as c:
        seed_review(c,original_rows())
        uid=c.execute("INSERT INTO users(username,email,password_hash,study_group) VALUES ('fallback-balanced','fb@example.invalid','hash','experimental') RETURNING user_id").fetchone()['user_id']
        ids=balanced_session_scenarios(c,uid,'experimental')
        training=c.execute("""INSERT INTO training_sessions(user_id,session_type,study_group,algorithm_version,scenario_ids)
            VALUES (%s,'training','experimental',%s,%s) RETURNING *""",(uid,VERSION,Jsonb(ids))).fetchone()
        for item in ids[:5]:
            c.execute("""INSERT INTO training_responses(session_id,scenario_id,user_answer,is_correct,confidence_level,response_time,difficulty_at_response)
                SELECT %s,scenario_id,is_phishing,1,4,10,'intermediate' FROM training_scenarios WHERE scenario_id=%s""",(training['session_id'],item))
        c.execute("DELETE FROM training_scenarios WHERE difficulty_level='advanced' AND matched_pair_id IS NULL")
        assert evaluate_session(c,training)==ids
        decision=c.execute('SELECT * FROM difficulty_evaluations').fetchone()
        assert (decision['proposed_difficulty'],decision['applied_difficulty'],decision['reason'])==('advanced','intermediate','target_scenarios_unavailable')
        assert balanced_plan_safe(c,ids)
        assert evaluate_session(c,training) is None


def test_control_connection_never_reads_performance_and_repeated_plan_same(postgres):
    with postgres() as c:
        seed_review(c,original_rows())
        class InventoryOnly:
            def execute(self,query,*args):
                assert 'training_responses' not in query and 'training_sessions' not in query
                return c.execute(query,*args)
        first=balanced_session_scenarios(InventoryOnly(),123,'control')
        assert balanced_session_scenarios(InventoryOnly(),999,'control')==first
        assert balanced_plan_safe(c,first)


def test_wrong_baseline_mix_rejected_server_side_before_response(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed_review(c,original_rows())
    client=register_client(app,postgres,'tampered-balance','experimental')
    client.get('/inbox')
    with client.session_transaction() as state:
        sid=state['training_session_id'];ids=stored_plan(postgres,state)
    with postgres() as c:
        truth={r['scenario_id']:r['is_phishing'] for r in c.execute('SELECT scenario_id,is_phishing FROM training_scenarios')}
        first=next(i for i in range(5) if truth[ids[i]]==1)
        last=next(i for i in range(5,10) if truth[ids[i]]==0)
        ids[first],ids[last]=ids[last],ids[first]
        c.execute('UPDATE training_sessions SET scenario_ids=%s WHERE session_id=%s',(Jsonb(ids),sid))
    assert open_item(client,ids[0]).status_code==200
    with client.session_transaction() as state:token=state['active_form_token']
    result=submit_item(client,dict(scenario_id=ids[0],user_answer=truth[ids[0]],reasoning='Synthetic rejection',confidence_level=4,form_token=token))
    assert result.status_code==409 and b'quota' not in result.data.lower()
    with postgres() as c:assert c.execute('SELECT count(*) AS n FROM training_responses').fetchone()['n']==0


def test_completed_historical_results_unchanged_when_new_plan_is_selected(postgres):
    from performance import session_results
    with postgres() as c:
        seed_review(c,original_rows())
        uid=c.execute("INSERT INTO users(username,email,password_hash,study_group) VALUES ('historic-result','hr@example.invalid','hash','experimental') RETURNING user_id").fetchone()['user_id']
        old=balanced_session_scenarios(c,uid,'experimental')
        saved=c.execute("""INSERT INTO training_sessions(user_id,session_type,study_group,algorithm_version,scenario_ids,completed_at)
            VALUES (%s,'training','experimental',%s,%s,CURRENT_TIMESTAMP) RETURNING session_id""",(uid,PAIR_VERSION,Jsonb(old))).fetchone()['session_id']
        c.execute("""INSERT INTO training_responses(session_id,scenario_id,user_answer,is_correct,reasoning,confidence_level,response_time,difficulty_at_response)
            SELECT %s,scenario_id,is_phishing,1,'Historical result preserved',4,19,difficulty_level
            FROM training_scenarios WHERE scenario_id=ANY(%s)""",(saved,old))
        tables=('users','training_sessions','training_responses','difficulty_evaluations','training_scenarios')
        before={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}
        result=session_results(c,uid,saved)
        next_plan=balanced_session_scenarios(c,uid,'experimental')
        assert balanced_plan_safe(c,next_plan)
        # Both never-completed intermediate items remain preferred when feasible.
        unused={r['scenario_id'] for r in c.execute("SELECT scenario_id FROM training_scenarios WHERE difficulty_level='intermediate' AND NOT(scenario_id=ANY(%s))",(old,))}
        assert unused.issubset(next_plan)
        assert session_results(c,uid,saved)==result
        assert before=={t:c.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in tables}


def test_approved_advanced_package_retains_original_introduction_version(monkeypatch):
    from scripts import integrate_advanced
    def forbidden():
        pytest.fail('Package verification must not access a database')
    monkeypatch.setattr(integrate_advanced,'get_db_connection',forbidden)
    rows=integrate_advanced.verified_package()
    assert len(rows)==8 and all(r['introduced_in_version']==PAIR_VERSION for r in rows)
