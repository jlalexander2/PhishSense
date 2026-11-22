"""Targeted pass: preserve foundations, neutral context and complete participant UI."""
import json
import re
from pathlib import Path
from html.parser import HTMLParser

from scenario_review import load_review,seed_review,PROTECTED
from adaptive import choose_schedule,CONTROL_SCHEDULE
from test_database import postgres
from test_control_schedule import application
from test_scenario_review import original_rows


def test_six_refinements_and_only_approved_grammar_change_preserve_foundations():
    prior=json.loads(Path('data/scenario_realism_revision3.json').read_text())
    old={r['source_id']:r['proposed'] for r in prior['scenarios']}
    grammar_id='evercrest-adv-draft-legit-003'
    assert 'For SD-4926, When both phones are available' in old[grammar_id]['email_body']
    old[grammar_id]['email_body']=old[grammar_id]['email_body'].replace(
        'For SD-4926, When both phones are available',
        'For SD-4926, when both phones are available')
    new=load_review()
    assert 'For SD-4926, when both phones are available' in new[grammar_id]['proposed']['email_body']
    changed={sid for sid,item in new.items() if item['proposed']!=old[sid]}
    assert changed=={'phish-0057','phish-0059','legit-004','legit-005','legit-008','legit-009'}
    foundations={'phish-0052','evercrest-adv-draft-phish-001','evercrest-adv-draft-legit-001',
        'evercrest-adv-draft-phish-002','evercrest-adv-draft-legit-002',
        'evercrest-adv-draft-phish-003','evercrest-adv-draft-legit-003',
        'evercrest-adv-draft-independent-phish-001'}
    assert not changed & foundations
    for sid,item in new.items():
        assert all(item['proposed'].get(k)==old[sid].get(k) for k in PROTECTED)


def test_all_context_records_are_neutral_and_all_labels_remain_provisional():
    for item in load_review().values():
        context=item['proposed']['training_context']
        assert not re.search(r'\b(must|never|prohibited|unauthorized|phishing|legitimate|suspicious|unsafe)\b|do not',context,re.I)
        assert item['participant_approval_required']
        assert item['reviewer_metadata']['empirical_difficulty_validated'] is False


def test_targeted_intermediate_evidence_is_available_without_rules():
    rows=load_review()
    account=rows['legit-004']['proposed']
    assert all(t in account['training_context'] and t in account['email_body'] for t in ('AC-482','EG-LT-27','Evercrest Mail'))
    renewal=rows['legit-005']['proposed']
    assert 'SW-240' in renewal['training_context'] and 'SW-240' in renewal['email_body']
    assert '$280' in renewal['training_context'] and '$280' in renewal['email_body']
    maintenance=rows['legit-008']['proposed']
    assert all(t in maintenance['training_context'] and t in maintenance['email_body'] for t in ('MNT-240','RPT-18','02:00','04:00'))
    statement=rows['legit-009']['proposed']
    assert '4482' in statement['training_context'] and '4482' in statement['email_body']
    assert 'P10' in statement['training_context'] and 'P10' in statement['email_body']


class Tags(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))


def test_every_database_scenario_renders_without_reviewer_or_active_content(postgres,monkeypatch):
    from flask import render_template
    app=application(postgres,monkeypatch)
    with postgres() as c:
        assert seed_review(c,original_rows())==27
        rows=c.execute('SELECT * FROM training_scenarios ORDER BY scenario_id').fetchall()
    assert len(rows)==27
    for row in rows:
        # A malicious accidental reviewer field must never get projected.
        row['reviewer_metadata']={'answer':'PRIVATE_REVIEW_ONLY'}
        with app.test_request_context('/training?item_ref='+'a'*64):
            page=render_template('training.html',scenario=row,username='Synthetic learner',form_token='fixture-token',item_ref='a'*64)
        assert row['source_id'] not in page and 'PRIVATE_REVIEW_ONLY' not in page
        assert 'Workplace context' in page and 'training.example/disabled-link' not in page
        parser=Tags();parser.feed(page)
        assert not any(tag in ('script','iframe','object','embed') for tag,attrs in parser.tags)
        assert not any(attrs.get('name') in ('scenario_id','source_id','difficulty_level','is_phishing') for tag,attrs in parser.tags)
        assert not any(attrs.get('href','').startswith(('https:','http:','javascript:','data:','mailto:')) for tag,attrs in parser.tags)
        assert not any('download' in attrs or any(k.lower().startswith('on') for k in attrs) for tag,attrs in parser.tags)
