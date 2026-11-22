"""Revision 3: no answer/ID leakage; safe equivalent inspection and pool viability."""
import copy
import json
from pathlib import Path
import secrets
from collections import Counter

import pytest
from jinja2 import Environment,FileSystemLoader,select_autoescape

from participant_refs import item_reference,resolve_reference
from scenario_review import load_review,seed_review
from email_presentation import present_email
from adaptive import choose_schedule,CONTROL_SCHEDULE
from test_database import postgres
from test_control_schedule import application,register_client
from test_scenario_review import original_rows
from item_helpers import stored_plan,reference,open_item,submit_item


def test_opaque_reference_binding_and_no_encoded_id():
    key=secrets.token_bytes(32)
    ref=item_reference(key,7,11,123,'nonce')
    assert len(ref)==64 and resolve_reference(key,7,11,[123,124],'nonce',ref)==123
    for user,sid,nonce in [(8,11,'nonce'),(7,12,'nonce'),(7,11,'other')]:
        assert resolve_reference(key,user,sid,[123,124],nonce,ref) is None
    assert resolve_reference(key,7,11,[124],'nonce',ref) is None
    assert resolve_reference(key,7,11,[123],'nonce','123') is None


def test_pair_inspection_parity_and_reviewer_fields_not_projected():
    rows=load_review()
    env=Environment(loader=FileSystemLoader('templates'),autoescape=select_autoescape(['html']))
    macro=env.get_template('email_content.html').module.content
    for sid in ('evercrest-adv-draft-phish-001','evercrest-adv-draft-legit-001'):
        s=copy.deepcopy(rows[sid]['proposed'])
        s['presentation_metadata']['expected_classification']='HIDDEN_REVIEW_ANSWER'
        view=present_email(s);html=str(macro(view))
        assert 'Application:' in html and 'Requested access' in html
        assert 'Destination:' in html and 'HIDDEN_REVIEW_ANSWER' not in html
        assert 'href=' not in html and '<script' not in html and '<input' not in html
    attack=copy.deepcopy(rows['evercrest-adv-draft-phish-001']['proposed'])
    attack['presentation_metadata']['links'][0]['permissions']=['<img src=x onerror=alert(1)>']
    html=str(macro(present_email(attack)))
    assert '<img' not in html and '&lt;img' in html
    attack['presentation_metadata']['reply_to']='evil@example.com'
    assert present_email(attack)['reply_to']==''


def test_all_27_audited_and_pool_capacity_unchanged():
    rows=load_review()
    assert len(rows)==27 and all(r['revision']==3 for r in rows.values())
    greetings=Counter(r['proposed']['email_body'].split('\n\n')[0] for r in rows.values())
    assert max(greetings.values())<10
    pools={level:[] for level in ('beginner','intermediate','advanced')}
    for i,item in enumerate(rows.values()):
        s=item['proposed'];pools[s['difficulty_level']].append(dict(scenario_id=i,matched_pair_id=s.get('matched_pair_id')))
        assert item['reviewer_metadata']['rating_status'].startswith('Current label retained')
    assert len(pools['intermediate'])==12
    assert choose_schedule(pools,('intermediate',)*10) is not None
    assert choose_schedule(pools,('advanced',)*5) is not None
    assert choose_schedule(pools,('advanced',)*6) is None
    assert choose_schedule(pools,CONTROL_SCHEDULE) is not None


def test_participant_html_cookie_raw_id_rejection_and_replay(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed_review(c,original_rows())
    client=register_client(app,postgres,'opaque','experimental')
    inbox=client.get('/inbox')
    with client.session_transaction() as state:
        ids=stored_plan(postgres,state);sid=state['training_session_id']
        assert 'training_scenario_ids' not in state and 'active_scenario_id' not in state
    assert b'scenario_id=' not in inbox.data
    assert client.get('/training?scenario_id='+str(ids[0])).status_code==302
    page=open_item(client,ids[0]);assert page.status_code==200
    assert b'name="scenario_id"' not in page.data and b'name="item_ref"' in page.data
    assert b'phish-' not in page.data and b'legit-' not in page.data
    assert b'Priority explicit reapproval' not in page.data
    with client.session_transaction() as state:
        assert 'training_scenario_ids' not in state and 'active_scenario_id' not in state
        token=state['active_form_token'];ref=state['active_item_ref']
    old_cookie=client.get_cookie(app.config['SESSION_COOKIE_NAME']).value
    payload=dict(item_ref=ref,user_answer=1,confidence_level=4,reasoning='Synthetic opaque workflow',form_token=token)
    assert client.post('/training',data={**payload,'scenario_id':ids[0]}).status_code==400
    assert client.post('/training',data=payload).status_code==200
    # Replaying the entire old signed cookie cannot append an answer to a new item.
    client.set_cookie(app.config['SESSION_COOKIE_NAME'],old_cookie)
    assert client.post('/training',data=payload).status_code in (302,400)
    with postgres() as c:
        assert c.execute('SELECT count(*) AS n FROM training_responses WHERE session_id=%s',(sid,)).fetchone()['n']==1


def test_reply_to_and_permissions_visible_only_as_safe_evidence(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:
        seed_review(c,original_rows())
        row=c.execute("SELECT presentation_metadata FROM training_scenarios WHERE source_id='phish-0052'").fetchone()
        assert row['presentation_metadata']['reply_to']=='remittance@bracken-settlement.example'
        cases=c.execute("SELECT presentation_metadata FROM training_scenarios WHERE matched_pair_id='evercrest-consent'").fetchall()
        assert all(s['presentation_metadata']['links'][0]['permissions'] for s in cases)
        assert c.execute("SELECT phishing_technique FROM training_scenarios WHERE source_id='phish-0075'").fetchone()['phishing_technique']=='Supplier impersonation and work-credential harvesting'


def test_legacy_missing_plan_is_preserved_and_new_start_explicit(postgres,monkeypatch):
    app=application(postgres,monkeypatch)
    with postgres() as c:seed_review(c,original_rows())
    client=register_client(app,postgres,'legacy-plan','experimental')
    with client.session_transaction() as state:uid=state['user_id']
    with postgres() as c:
        legacy=c.execute("INSERT INTO training_sessions(user_id,session_type) VALUES (%s,'training') RETURNING *",(uid,)).fetchone()
    with client.session_transaction() as state:
        state['training_session_id']=legacy['session_id']
        state['training_scenario_ids']=[101,102]
    page=client.get('/inbox')
    assert page.status_code==409 and b'no saved scenario plan' in page.data
    assert b'action="/training/start"' in page.data and b'Start a new session' in page.data
    with client.session_transaction() as state:
        token=state['start_training_token']
        assert 'training_scenario_ids' not in state
    assert client.post('/training/start',data={'form_token':token}).status_code==302
    with postgres() as c:
        assert c.execute('SELECT * FROM training_sessions WHERE session_id=%s',(legacy['session_id'],)).fetchone()==legacy
        assert c.execute('SELECT count(*) AS n FROM training_sessions').fetchone()['n']==2
