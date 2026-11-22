from item_helpers import stored_plan, open_item, submit_item, reference
"""Review corpus is explicit, isolated, complete, and never overwrites history."""
import json
from html import unescape
from pathlib import Path
import pytest
from scenario_review import load_review,seed_review,PROTECTED
from email_presentation import present_email,safe_destination
from test_database import postgres
from test_control_schedule import application,register_client
from adaptive import CONTROL_SCHEDULE,pair_safe


def original_rows():
    allowed=('sender_name','sender_email','subject','email_body','is_phishing','difficulty_level','explanation','phishing_intent','phishing_technique','target_category','source_id','training_context','learning_objectives','matched_pair_id','introduced_in_version')
    return [dict(scenario_id=101+i,**{k:s.get(k) for k in allowed}) for i,s in enumerate(map(json.loads,Path('data/scenarios_approved_for_prototype.jsonl').read_text().splitlines()))]


def test_revision_content_complete_and_evidence_defensible():
    review=load_review()
    assert len(review)==27
    for item in review.values():
        s=item['proposed'];body=s['email_body']
        assert s['review_status']=='draft' and item['participant_approval_required']
        assert item['difficulty_rationale'] and s['training_context'] and s['explanation']
        assert item['reviewer_metadata']['approval_required']
        assert 'must not' not in s['training_context'].lower()
        assert 'must verify' not in s['training_context'].lower()
        assert len(body.split())>=35
        assert 'training.example' not in body and 'simulated' not in body.lower()
        assert s['sender_email'].split('@')[1].endswith('.example')
        for part in present_email(s)['parts']:
            if part['kind']=='link':assert safe_destination(part['destination'])
    first=review['phish-0052']['proposed']
    assert '7042' in first['training_context'] and '9168' in first['email_body']
    assert '9168' in first['explanation'] and '7042' in first['explanation']
    assert first['presentation_metadata']['reply_to']=='remittance@bracken-settlement.example'
    assert 'diversion' in first['phishing_technique']
    second=review['phish-0075']['proposed']
    assert 'billing.ridgehaven-components.example' in second['training_context']
    assert 'accounts.ridgehaven-review.example' in second['email_body'] and 'password' in second['email_body']
    assert first['sender_email']!=second['sender_email']
    # Links/attachments occur in both classes; no one-class-only UI shortcut.
    for label in (0,1):
        kinds={p['kind'] for item in review.values() if item['proposed']['is_phishing']==label for p in present_email(item['proposed'])['parts']}
        assert {'link','attachment'}.issubset(kinds)
    # A coarse confound check, not a definition or empirical rating of difficulty.
    for level in ('beginner','intermediate','advanced'):
        lengths=[[len(item['proposed']['email_body'].split()) for item in review.values()
                  if item['proposed']['difficulty_level']==level and item['proposed']['is_phishing']==label]
                 for label in (0,1)]
        assert max(map(min,lengths)) <= min(map(max,lengths))


def test_review_loader_preserves_numeric_ids_and_refuses_history(postgres):
    rows=original_rows();original={r['scenario_id']:r for r in rows}
    with postgres() as c:
        assert seed_review(c,rows)==27
        actual=c.execute('SELECT * FROM training_scenarios ORDER BY scenario_id').fetchall()
        assert set(r['scenario_id'] for r in actual)==set(original)
        for r in actual:
            assert all(r.get(k)==original[r['scenario_id']].get(k) for k in PROTECTED)
        before=actual
        with pytest.raises(ValueError,match='nonempty'):
            seed_review(c,rows)
        assert c.execute('SELECT * FROM training_scenarios ORDER BY scenario_id').fetchall()==before
        assert c.execute('SELECT count(*) AS n FROM training_responses').fetchone()['n']==0


def test_review_loader_rejects_protected_metadata_changes(postgres):
    rows=original_rows();rows[0]['is_phishing']=1-rows[0]['is_phishing']
    with postgres() as c:
        with pytest.raises(ValueError,match='metadata'):
            seed_review(c,rows)
        assert c.execute('SELECT count(*) AS n FROM training_scenarios').fetchone()['n']==0


@pytest.mark.parametrize('group',['experimental','control'])
def test_revised_corpus_full_workflow(postgres,monkeypatch,group):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed_review(c,original_rows())
    client=register_client(app,postgres,'review-'+group,group)
    assert client.get('/review').status_code==404  # Review route is launcher-only.
    assert client.get('/inbox').status_code==200
    with client.session_transaction() as state:sid=state['training_session_id']
    done=[]
    for position in range(10):
        with client.session_transaction() as state:ids=stored_plan(postgres,state)
        selected=next(i for i in ids if i not in done)
        page=open_item(client,selected)
        assert page.status_code==200 and b'Workplace context' in page.data
        assert b'training.example/disabled-link' not in page.data and b'[Simulated' not in page.data
        with client.session_transaction() as state:
            token=state['active_form_token'];state['scenario_started_at']=__import__('time').time()-10
        with postgres() as c:
            scenario=c.execute('SELECT * FROM training_scenarios WHERE scenario_id=%s',(selected,)).fetchone()
        # Strong adaptive learner and low-performing control retain their protocols.
        feedback=submit_item(client,dict(scenario_id=selected,user_answer=scenario['is_phishing'] if group=='experimental' else 1-scenario['is_phishing'],confidence_level=5 if group=='experimental' else 1,reasoning='Synthetic revised-content workflow',form_token=token))
        assert feedback.status_code==200
        assert scenario['explanation'] in unescape(feedback.data.decode())
        done.append(selected)
    with postgres() as c:
        responses=c.execute('SELECT * FROM training_responses WHERE session_id=%s ORDER BY response_id',(sid,)).fetchall()
        expected=('intermediate',)*5+('advanced',)*5 if group=='experimental' else CONTROL_SCHEDULE
        assert tuple(r['difficulty_at_response'] for r in responses)==expected
        assert len(set(done))==10 and pair_safe(c,done)
        assert all(r['reasoning']=='Synthetic revised-content workflow' for r in responses)
        assert c.execute('SELECT completed_at FROM training_sessions WHERE session_id=%s',(sid,)).fetchone()['completed_at'] is not None
    assert client.get('/results?session_id='+str(sid)).status_code==200


@pytest.mark.parametrize('fault',['missing_target','wrong_project','public_schema','no_tls'])
def test_review_seed_guard_prevents_unsafe_writes(monkeypatch,fault):
    from unittest.mock import MagicMock
    conn=MagicMock()
    conn.info.host='db.'+'b'*20+'.supabase.co'
    conn.info.user='postgres';conn.info.port=5432;conn.info.dbname='postgres'
    conn.pgconn.ssl_in_use=True
    conn.execute.return_value.fetchone.return_value={'name':'public'}
    monkeypatch.setenv('TEST_DATABASE_URL','postgresql://postgres@db.'+'b'*20+'.supabase.co/postgres')
    if fault=='missing_target':monkeypatch.delenv('TEST_DATABASE_URL')
    if fault=='wrong_project':conn.info.host='db.'+'a'*20+'.supabase.co'
    if fault=='no_tls':conn.pgconn.ssl_in_use=False
    with pytest.raises(ValueError):seed_review(conn,original_rows())
    statements=[str(call.args[0]) for call in conn.execute.call_args_list]
    assert not any('INSERT' in s or 'UPDATE' in s or 'DELETE' in s for s in statements)
