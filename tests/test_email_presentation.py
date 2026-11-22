import copy
import hashlib
import json
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from email_presentation import safe_destination, body_parts, present_email

ENV = Environment(loader=FileSystemLoader('templates'), autoescape=select_autoescape(['html']))


def render(scenario):
    macro = ENV.get_template('email_content.html').module.content
    return str(macro(present_email(scenario)))


@pytest.mark.parametrize('url', [
    'https://payroll.evercrest-group.example/employee/statement',
    'https://evercrest-cl0ud.example/account/recovery',
    'https://workspace.alderbridge.test/Harbor/review?folder=42#comments',
])
def test_fictional_https_destinations_accepted(url):
    assert safe_destination(url)


@pytest.mark.parametrize('url', [
    'http://payroll.example/account', 'javascript:alert(1)', 'data:text/html,test',
    'https://real.com/path', 'https://example.com/path', 'https://example',
    'https://foo.example.real.com/path', 'https://user:password@foo.example/path',
    'https://foo.example:443/path', 'https://127.0.0.1/path',
    'https://foo.example/\npath', 'https://foo.example/%0apath',
    'https://foo.example\\@real.com/path', 'https://föö.example/path',
    'https://foo.example./path', '//foo.example/path',
])
def test_unsafe_or_ambiguous_destinations_remain_text(url):
    assert not safe_destination(url)
    html = render(dict(email_body='[[link:Open document|'+url+']]'))
    assert 'email-link-inspection' not in html
    assert 'href=' not in html


def test_link_inspection_has_no_navigation_or_secret_target():
    body = 'Please review:\n[[link:View Payroll Statement|https://payroll.evercrest-group.example/employee/statement]]\nRegards,\nPayroll Operations'
    html = render(dict(email_body=body))
    assert '<summary' in html and 'View Payroll Statement' in html
    assert 'title="https://payroll.evercrest-group.example/employee/statement"' in html
    assert 'Destination: https://payroll.evercrest-group.example/employee/statement' in html
    assert 'href=' not in html and 'onclick=' not in html and 'download=' not in html
    assert '<script' not in html and '<form' not in html


def test_sender_content_cannot_turn_labels_or_files_into_html():
    body = '[[link:<img src=x onerror=alert(1)>|https://folder.example/review]]\n[[attachment:<script>alert(2)</script>.pdf|<iframe src=x>]]'
    html = render(dict(email_body=body))
    assert '<img' not in html and '<script' not in html and '<iframe' not in html
    assert '&lt;img' in html and '&lt;script&gt;' in html


def test_legacy_attachment_keeps_warning_extension_and_preview():
    body = '[simulated attachment: shipping_form.exe — not downloadable]\n[Simulated attachment: packs.zip; contents preview: A.pdf, B.pdf — not downloadable]'
    parts = body_parts(body)
    files = [p for p in parts if p['kind'] == 'attachment']
    assert [p['filename'] for p in files] == ['shipping_form.exe', 'packs.zip']
    assert files[1]['preview'] == 'contents preview: A.pdf, B.pdf'
    html = render(dict(email_body=body))
    assert 'shipping_form.exe' in html and 'packs.zip' in html
    assert 'simulated attachment' not in html.lower() and 'not downloadable' not in html
    assert '<a' not in html and 'download=' not in html


def test_context_removed_only_on_exact_match_without_mutation():
    context = 'Existing directory: workspace.alderbridge.example'
    body = 'TRAINING CONTEXT (not part of the email):\n'+context+'\n\nEMAIL MESSAGE:\nHello,\n\nReview the pack.'
    source = dict(training_context=context, email_body=body)
    before = copy.deepcopy(source)
    view = present_email(source)
    assert view['context'] == context
    assert view['parts'] == [dict(kind='text', text='Hello,\n\nReview the pack.')]
    assert source == before
    source['training_context'] = 'Different context'
    assert present_email(source)['parts'][0]['text'].startswith('TRAINING CONTEXT')


def test_classification_difficulty_group_and_ids_do_not_change_rendering():
    base = dict(email_body='Hello,\n[[link:Open review|https://workspace.partner.example/review]]\n[[attachment:report.pdf]]', training_context='Expected workplace task')
    expected = render(base)
    for label in (0, 1):
        for level in ('beginner','intermediate','advanced'):
            for group in ('control','experimental'):
                assert render(dict(base, is_phishing=label, difficulty_level=level,
                    study_group=group, source_id='unrelated', scenario_id=999)) == expected


def test_drafts_cannot_replace_approved_records_or_invalidate_pairs():
    from import_scenarios import validate_scenarios
    path = Path('data/scenarios_approved_for_prototype.jsonl')
    draft = json.loads(Path('data/scenario_realism_drafts.json').read_text())
    assert draft['base_dataset_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    originals = {s['source_id']:s for s in map(json.loads,path.read_text().splitlines())}
    assert len(draft['scenarios']) == len(originals) == 27
    proposed = []
    for item in draft['scenarios']:
        original = originals[item['source_id']]
        assert item['base_sha256'] == hashlib.sha256(json.dumps(original,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        changed = item['proposed']; proposed.append(changed)
        for key in ('source_id','is_phishing','difficulty_level','matched_pair_id','learning_objectives'):
            assert changed.get(key) == original.get(key)
        assert changed['review_status'] == 'draft' and item['review_notes']
        assert changed['sender_email'].split('@')[1].endswith(('.example','.test'))
        assert 'training.example' not in changed['email_body']
        assert 'simulated ' not in changed['email_body'].lower()
        for part in present_email(changed)['parts']:
            if part['kind'] == 'link': assert safe_destination(part['destination'])
    assert validate_scenarios(proposed)  # Importer rejects all unapproved revisions.
    pairs = {}
    for s in proposed:
        if s.get('matched_pair_id'):pairs.setdefault(s['matched_pair_id'], []).append(s)
    assert len(pairs) == 3 and all(len(v) == 2 for v in pairs.values())
