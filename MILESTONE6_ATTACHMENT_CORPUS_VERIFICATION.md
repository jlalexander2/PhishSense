# Milestone 6 manual verification: static attachments and corpus routing

November 22, 2026. Attachment inspection is deferred to Milestone 7. Current
Milestone 6 status remains: **Implementation substantially complete — final
database regression testing and manual browser verification pending.**

## Static behavior and safety

`email_presentation.py` parses attachment filenames and optional preview text.
`templates/email_content.html` renders a static span/strong tile with an optional
escaped text preview beneath the filename. It has no button/link, click handler,
file endpoint, download, script, embedded document or resource element. Clicking
is intentionally inert. No hidden expandable preview is currently supported.
Preserving a filename such as invoice.exe does not supply or execute an executable.

Current local corpora contain six base attachments (one with preview text) and
nine refined attachments (eight with preview text). Preview text is encoded in
attachment tokens in the email body, not in a separate hidden attachment metadata
collection. The sole refined item without preview text is Invoice_3921.exe.
The future plan is [MILESTONE7_ATTACHMENT_INSPECTION_PLAN.md](MILESTONE7_ATTACHMENT_INSPECTION_PLAN.md).

This verification reran only database-free checks:

- `tests/test_email_presentation.py`: **25 passed**, 0.11 seconds, no skips.
- DOM inspection of all **15 base/refined attachment cards**: only span/strong
  elements and class attributes; no navigation/download, event handlers or
  resource elements. Preview/filename strings remain escaped.
- Chrome hostile-content smoke check: **passed**, with hostile text escaped,
  no injected script/frame/image and zero unsafe-resource requests. No database
  connections were used.

These are existing cases, not 25 new distinct suite passes. The overall checkpoint
remains **126 distinct passing cases, one connection-blocked case and 32 database
cases not rerun**, out of 159 collected. No database tests were resumed.

## Why payment.doc appeared

The base approved file `data/scenarios_approved_for_prototype.jsonl` contains
`phish-0059` with `payment.doc` and no preview text. The separate refined candidate
in `data/scenario_realism_drafts.json` retains the same source ID but uses
`FAC-91_payment.doc`, with preview text “Facilities reference FAC-91. Amount:
$15,000.” Neither the source identity nor the answer/difficulty changed.

The normal app queries `training_scenarios` through `get_db_connection()`; it does
not load the refined JSON or apply an automatic presentation overlay. Normal
connections use DATABASE_URL, not TEST_DATABASE_URL. Refined local content has
not replaced the stored normal-app corpus. Editing/reviewing the JSON alone
cannot change an email served from PostgreSQL.

A credential-safe local process inspection found:

| Port | Recognized launcher | Meaning |
|---|---|---|
| 5000 | app.py | Normal database-backed app, not the refined review launcher |
| 5001 | browser_e2e.py | Earlier browser-test process; do not assume current corpus/code |
| 5003 | recording_demo.py | Earlier prepared demo; do not assume current corpus/code |
| 5005 | Not identified from the allowed script-name list | No corpus assertion made |
| 5006–5008 | serve_scenario_review.py | Separate retained review snapshots |

Saved review state files map ports 5006, 5007 and 5008 to previous review runs.
**None of their saved content hashes matches the current refined JSON.** This
proves they are not confirmed current snapshots; it does not identify every
row difference. In particular, port 5008 predates the final capitalization fix.
The process inspection printed only known script names, not arguments/secrets.

If the participant browser is on port 5000, the older filename is consistent with
normal database-backed corpus routing rather than failure to show an attachment
preview. If on an older demo/review port, its retained snapshot must be checked.
The current browser URL was not supplied in this request. No live database row,
process environment, current search_path or project identity was re-queried, so
this is a code/process/file audit, not a claim to have reverified the precise live
database contents. No authenticated training/inbox requests were made because
those routes can create or advance training state.

## Safe ways to inspect the refined corpus

**Available now, without database writes:**
`/private/tmp/PHISHSENSE_FINAL_REVIEW.html` was refreshed from the current refined
JSON using `scripts/preview_scenario_realism.py`. It uses the same email-content
macro, requires no database, and is deliberately reviewer-only: it displays
answers, IDs and review notes. Never give it to participants or treat it as a full
login/training workflow test.

**Participant workflow review, only after explicit database-write approval:**
Use a fresh isolated namespace in the verified distinct disposable TEST project,
seed only scenario presentation data plus new synthetic users, and launch a fresh
loopback review process with a distinct cookie. Do not copy participant accounts,
history or research results, replace normal-app records, or reseed an old sandbox.
Preserve previous review/manual namespaces and their records. The current
`serve_scenario_review.py` already verifies target separation, uses production only
for a read-only scenario source, and creates its own TEST schema; launching it is
not a database-free action and is **not performed or newly authorized here**.
Its review index is researcher-only; learner testing uses its separate login and
normal participant routes. Existing running processes may retain pre-v4 code.

No database connection, schema creation, scenario activation, server restart or
history change occurred during this audit. No application/scenario code was
modified. No commit, push, deployment or Milestone 7 implementation occurred.
