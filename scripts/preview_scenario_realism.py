"""Create a local, researcher-review-only preview. Never imports or queries a DB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from email_presentation import present_email


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='/private/tmp/PHISHSENSE_EMAIL_REALISM_REVIEW.html')
    args=parser.parse_args()
    draft=json.loads((ROOT/'data/scenario_realism_drafts.json').read_text())
    assert hashlib.sha256((ROOT/'data/scenarios_approved_for_prototype.jsonl').read_bytes()).hexdigest()==draft['base_dataset_sha256']
    env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=select_autoescape(['html']))
    # Explicit autoescape for this string template too; no email data marked safe.
    env.autoescape=True
    style=(ROOT/'templates/training.html').read_text().split('<style>',1)[1].split('</style>',1)[0]
    template=env.from_string('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; form-action 'none'; base-uri 'none'; object-src 'none'; frame-src 'none'"><title>PhishSense — DRAFT scenario review</title><style>STYLE</style></head><body><main style="max-width:1000px;margin:30px auto;padding:24px"><h1>DRAFT scenario review — not participant content</h1><p>These revisions are not approved, imported, or used in training. All classification labels and review notes below are reviewer-only.</p>{% from 'email_content.html' import content %}{% for item in drafts %}{% set s=item.proposed %}{% set view=present_email(s) %}<section style="margin:40px 0"><h2>{{ s.source_id }} — {{ 'Phishing' if s.is_phishing else 'Legitimate' }} / {{ s.difficulty_level }}</h2><ul>{% for note in item.review_notes %}<li>{{ note }}</li>{% endfor %}</ul>{% if item.reviewer_metadata is defined %}<p><strong>Calibration:</strong> {{ item.reviewer_metadata.calibration_note }}</p>{% endif %}<aside class="email-context"><h3>Workplace context</h3><p>{{ view.context }}</p></aside><div class="email-card"><div class="email-header"><h3 class="email-subject">{{ s.subject }}</h3><div class="email-detail"><strong>From:</strong> {{ s.sender_name }} &lt;{{ s.sender_email }}&gt;</div>{% if view.reply_to %}<div class="email-detail"><strong>Reply-To:</strong> {{ view.reply_to }}</div>{% endif %}<div class="email-detail"><strong>To:</strong> You</div></div><div class="email-body">{{ content(view) }}</div></div><details><summary>Revised explanation — requires approval</summary><p>{{ s.explanation }}</p></details></section>{% endfor %}</main></body></html>'''.replace('STYLE',style))
    path=Path(args.output)
    path.write_text(template.render(drafts=draft['scenarios'],present_email=present_email))
    print('Draft-only preview created:',path)
    print('No database access, approvals, imports or application changes performed.')


if __name__=='__main__':main()
