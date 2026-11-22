# Milestone 6 — Security and Functional Verification

**Status: Implementation substantially complete — final database regression testing and manual browser verification pending.**

Feature development is stopped. Current handoff and T25–T30 checklist:
[MILESTONE6_HANDOFF.md](MILESTONE6_HANDOFF.md). Current validation is 126 distinct
passes out of 159 cases, one connection-blocked case and 32 database cases not
rerun; zero reported assertion failures and zero skips. Older records below are
historical evidence, not a complete pass for the latest build. The published
release remains v0.5.0. The prepared local build is v0.6.0; its new-session
protocol remains rules-v4-balanced-selection. Staging/commit approval is pending.

## T25 — Dashboard progress summaries

The authenticated dashboard reuses Milestone 5 `learner_history` calculations in
a read-only transaction. It displays completed sessions, recorded responses in
completed sessions, response-weighted accuracy, average elapsed response time,
average confidence, a link to the latest completed result, and the latest versus
previous completed-session accuracy change in percentage points. In-progress
sessions are counted separately and excluded from performance statistics. Empty
history displays an explanation and dashes rather than invented percentages.

The same learner-ownership filters and completed-session definition as results
and history apply. Opening the dashboard does not mark sessions complete or
backfill historical records. No new analytics table or migration is required.

## T26 — Input and simulated-content safety

- Registration validates email syntax, a nonempty username up to 80 characters,
  email up to 254 characters, and a nonempty password up to 1024 characters.
  Controls/NUL characters are rejected where incompatible with database text.
  Existing hashes and password hashing are unchanged; no passwords are reset.
- Login validates field size and rejects NUL input before database access. Its
  account query remains parameterized and its failure message remains generic.
- Request bodies are limited to 64 KiB; repeated form keys are rejected as
  ambiguous. Training still requires binary classification, confidence 1–5,
  nonblank reasoning up to 5000 characters, the correct active scenario, and a
  matching form token. NUL reasoning is rejected without altering valid text.
- Scenario/result identifiers are bounded to PostgreSQL INTEGER IDs. Nonfinite,
  boolean, missing or future training start times cannot create response metrics.
- Scenario content, context, feedback and reasoning use Jinja HTML escaping.
  Email HTML remains escaped. The realism refinement adds inert fictional-link
  inspection and attachment cards without hrefs, navigation or downloads; see
  SCENARIO_REALISM.md. Other strings remain text.
- A response Content Security Policy disables scripts, frames, objects, external
  resources, base URL changes and cross-origin form actions; framing is denied.
  Inline CSS remains permitted for the existing template styles. Responses also
  set `nosniff`, `no-referrer`, and `Cache-Control: no-store`.

A separate Chrome smoke check renders a hostile synthetic email locally without
any database connection. It checks the browser DOM and records attempted injected
resource requests. The initial run passed: escaped text, no injected executable
script/frame/image, and zero unsafe-resource requests.

```bash
.venv/bin/python scripts/verify_content_safety.py
# Other platforms: add --chrome /path/to/installed/chrome
```

The smoke check requires an installed Chrome binary, uses a temporary profile and
loopback server, and does not require Playwright or change application data.

## T27 — Complete classification and feedback workflow

Existing integration coverage executes all ten ordered responses, checks the
presented scenario, recorded correctness, required reasoning, confidence, elapsed
time, actual difficulty, immediate feedback, progress, and atomic completion.
Invalid, stale, skipped and replayed submissions cannot append a response.
New coverage submits hostile reasoning through the real workflow, verifies it
remains preserved as text, and checks scenario/feedback escaping and headers.

## T28 — Adaptive progression and fallback

The approved Milestone 4 algorithm, thresholds and protocol identifiers are
unchanged. Existing tests cover promotion/demotion boundaries, difficulty limits,
unused-scenario preference, pair exclusion, legacy-session protection and control
independence. New tests verify that fewer than five responses create no decision,
that four hard scenarios cannot fill five remaining positions, that the proposed
promotion is recorded but the original intermediate plan is retained, and that
the decision is idempotent. An undersized baseline cannot create a shortened
session. Existing control-inventory tests verify unavailable hard scenarios or
pair conflicts block activation instead of changing the fixed schedule.

## T29 — Authentication, isolation and sessions

Login, registration and logout POSTs require a browser-session-bound form token.
Token comparisons handle non-ASCII input safely. Login clears pre-login session
state. Logout GET now shows a confirmation form; only a valid protected POST
clears the session. Existing navigation links still lead to Log Out.

Session cookies are explicitly HttpOnly and SameSite=Lax. For local HTTP,
Secure remains off; configure `PHISHSENSE_HTTPS=true` only when serving over
HTTPS. This does not change PostgreSQL TLS, which remains `verify-full`.
No local `.env` values were changed.

Tests cover missing/wrong tokens, oversized and ambiguous forms, Unicode tokens,
unsigned/tampered cookies, logout invalidation, SQL-injection-shaped login input,
foreign-session results, and a wrong-owner training-session reference that cannot
read or append the other learner's responses. All data queries remain scoped to
the authenticated learner. No browser-supplied research-group assignment is used.

## T30 — Database integrity and research-group separation

The complete suite is run using `scripts/validate_milestone5.py`; despite its
historical filename, it discovers all current tests, including Milestone 6.
`TEST_DATABASE_URL` must explicitly identify a different Supabase project from
`DATABASE_URL`. No production fallback is allowed. An authenticated,
certificate-verified test connection is checked before schema creation.

Fixtures create only generated `phishsense_test_*` schemas in the disposable
project and remove them afterward. Production access is read-only, for before/
after hashes of the five public application tables. Tests use synthetic records,
including any deliberate deletes/updates in integrity fixtures. They do not
change real participant records or study assignments.

Both groups retain ten ordered emails, five intermediate baseline responses,
the approved experimental decision rules, and control's fixed sequence:
intermediate ×5, easy, hard, intermediate, easy, hard. Existing full group workflows
and pair-exclusion tests remain regression requirements.

```bash
.venv/bin/python scripts/validate_milestone5.py
```

## Validation record

- New offline rejection/security checks: 16 passed, 8 database cases deselected.
  This is preliminary evidence, not a substitute for the complete suite.
- Chrome synthetic-content smoke check: passed; zero unsafe-resource requests.
- Full integration run on November 22, 2026: **82 passed, 1 failed, 1 teardown
  error** in 318.06 seconds; stopped at the first failed test. Ten cases were not
  reached in that run. No skip was reported before stopping.
- The blocked case was the existing
  `test_tenth_response_completes_before_inbox_and_allows_next_session` in
  `tests/test_performance.py`. Both its call and teardown reported connection
  errors (`OperationalError`), rather than an assertion failure. This does not
  establish an application-logic defect, but the case is not validated for this
  build. The underlying connectivity cause has not been determined.
- The post-run production snapshot also could not connect. Production access in
  the runner was read-only; the final before/after hash equality is **not
  verified** for this run.
- Failed teardown means a generated test schema may remain in the disposable
  project. Cleanup is **not confirmed**. Do not drop arbitrary schemas or assume
  that the failed teardown succeeded.
- The ten unreached cases were checked separately without any database access:
  **10 passed** in 0.17 seconds (three rendered-template cases and seven
  target-guard cases). Across both runs, 92 distinct tests passed; the single
  connection-blocked workflow and failed teardown still prevent full sign-off.

The original run stopped without an automatic retry. On the user's subsequent
explicit request to investigate and resume, the distinct test project authenticated
with verified TLS and DNS resolved. The one leftover schema was rechecked against
the failed synthetic fixture and removed only in that disposable project. The
formerly blocked test then passed (1 passed in 23.54 seconds), production hashes
matched, and generated test-schema count was zero. The original outage's root
cause remains unproven. The subsequent 118-case regression run failed on a different existing test;
full-suite sign-off remains blocked. See SCENARIO_REALISM.md for the separate
connectivity review and the latest exact results.

No production migrations, imports, password resets, historical edits, protocol
changes, server restarts, Git commits or releases are performed by this work.

## Scope and remaining review

This is capstone functional/security verification, not a penetration-test or a
claim of production deployment readiness. Existing legacy sessions without a
completion timestamp are not silently repaired. Time measurements remain elapsed
time, including interruptions. The eight advanced scenarios still have no spare
capacity for the five-hard experimental branch under pair exclusion.

HTTPS hosting, deployment-level rate limiting, account recovery, email ownership
verification, centralized session revocation and a least-privilege deployed
backend role remain outside this milestone. Flask's signed cookies do not provide
server-side revocation of an already-copied cookie; logout clears the browser's
cookie. No researcher dashboard, exports or participant protocol changes were
introduced.

Older scripted account clients must first GET the account form and submit its
rendered `auth_form_token`; browser forms already do this. Existing local demo
launchers should be reviewed for that change before being restarted.

Manual review of the updated dashboard and logout confirmation in the intended
browser remains recommended. Already-running local sandboxes retain their
previous imported code until deliberately restarted; this task does not reset
them or recreate existing synthetic accounts.

## Email realism refinement

See [SCENARIO_REALISM.md](SCENARIO_REALISM.md) for the renderer, safety model,
review-required corpus changes and connectivity investigation. The 27 proposed
revisions are explicitly draft-only; approved source data and production remain
unchanged. All 25 new presentation tests pass, and the updated Chrome hostile
content/inert-link smoke check passes. No content-version policy or production
import is implemented implicitly.

### Latest refinement validation — November 22, 2026

- Full 118-case run: **106 passed, 1 failed, 1 teardown error** in 289.54 seconds,
  stopped at the first failure. No skip was reported before stopping.
- Blocked case: `test_empty_views_and_start_action_security` in
  `tests/test_performance.py`; both call and teardown reported connection errors,
  not an assertion failure. Eleven cases were not reached.
- Ten unreached offline template/target-guard cases passed separately in 0.17
  seconds. The remaining unreached ten-response completion case had already
  passed the targeted run (23.54 seconds) against this refinement.
- Thus 117 distinct current tests have successful evidence across these runs;
  the one connection-blocked start-action test has no successful current-build
  result. This is **not** a full-suite pass.
- All 25 new presentation tests passed within the full run. Updated Chrome
  hostile-content/link/attachment verification also passed.
- The final production snapshot could not connect. No production writes were
  performed, but final hash equality is unverified for this latest full run.
- Failed teardown may have left another generated schema. Its count/identity
  and cleanup are unverified. No more database operations were attempted.

The earlier verified leftover schema was removed before this run; that cleanup
is not proof of cleanup after the new failure. Obtain test-project pooler/status
evidence before resuming. Once verified healthy, inspect and remove only the
identified failed synthetic schema, rerun the blocked workflow and full suite,
and verify final cleanup and production hashes. Never use production as fallback.

## SQLSTATE review and resumed validation — November 22, 2026

The user reported six PostgreSQL log entries comprising two occurrences each of
23505, 23514 and 23503. These match deliberate negative tests:

| SQLSTATE | Intentional trigger | Expected handling |
|---|---|---|
| 23505, unique violation | `test_workflow` registers the same synthetic username/email twice | Flask catches `psycopg.errors.UniqueViolation` and returns Registration Failed; the test expects that response |
| 23514, check violation | `test_constraints_and_rollback` inserts session_type `invalid` | `pytest.raises(CheckViolation)` catches it; the test verifies the transaction rolled back the preceding user insert |
| 23503, foreign-key violation | The same integrity test references nonexistent user 999 | `pytest.raises(ForeignKeyViolation)` catches it; the connection context rolls back |

The driver exception classes expose these exact SQLSTATEs. The resumed negative
tests passed, so these deliberate failures were handled as expected. PostgreSQL
may log a rejected statement even when the application/test catches it. Two
executions of this test pair are consistent with the six reported entries. Exact
event attribution would additionally require matching the temporary schema or
statement; timestamps and constraint names alone do not prove every event's source.
These SQLSTATEs are not an explanation for an uncaught OperationalError.

Before resuming, a read-only diagnostic verified separate project identities,
session-pooler port 5432, three DNS addresses, certificate-verified authentication,
9 database activity entries and `max_connections=60`. Production and test use
different pooler hostnames. This does not establish either pooler's client limit
or the cause of the earlier transport failures.

One generated schema remained, containing exactly the latest failed synthetic
fixture: 19 scenarios, one `fresh` account, zero sessions, zero responses and zero
evaluations. The account could still be unassigned because the original failure
interrupted setup before its group update committed. Its identity, complete table inventory
and counts were rechecked before dropping only that schema in the disposable
project. No manual sandbox or production schema was removed.

Resumed validation uses sequential bounded batches with the same fixtures, TLS
and separate-project guard. It does not disable assertions or skip cases. A
private diagnostic wrapper reports only safe exception types, SQLSTATEs and fixed
error categories, and counts real connection objects without retaining them.
Each batch compares read-only production hashes and checks generated-schema
cleanup. No automatic retry is made on error.

- Batch 1: 19 passed in 66.33 seconds; zero failures/skips. Includes integrity,
  performance and target-guard cases, including both previously interrupted
  workflows. 139 observed test connections opened, peak one simultaneously open,
  none left open. Production hashes matched; generated test schemas: zero.
- Batch 2: 50 passed in 142.42 seconds; zero failures/skips. Adaptive, fixed-control
  and presentation cases. 291 observed test connections opened, peak one
  simultaneously open, none left open. Production hashes matched; generated
  test schemas: zero.
- The third batch selected 51 cases, including the two integrity cases already
  checked in batch 1. It passed 36, then had one fixture-setup error; 14 were not
  reached. Runtime: 114.15 seconds. The blocked setup was
  `test_dashboard_empty_state_no_invented_score`. Safe diagnostics captured
  `OperationalError`, SQLSTATE None, category **connection refused**, from
  `psycopg.connect()`; the cleanup connection also failed (fixture line 62).
  This occurred before scenario/test SQL could run. 239 observed connections
  had opened, peak one simultaneously open, none left open. The final production
  snapshot in that process also received connection refused.
- Independent read-only stability probe: passed for **365.78 seconds**, with
  36 held-connection checks and 36 freshly authenticated verified-TLS
  connections, at most two probe connections simultaneously. The probe stayed
  healthy while the other process reported refusal; this rules out attributing
  that failure to a query's expected SQLSTATE, but does not locate the
  network/pooler/local-egress cause.
- After the probe passed, a fresh verified process found one empty generated
  schema from the failed setup, checked it contained no records/objects, and
  removed only that schema. Production hashes matched across cleanup.
- Final controlled fresh-process run: **15 passed in 36.29 seconds**, zero
  failures/skips. 70 observed connections opened, peak one simultaneously open,
  none left open. Production hashes matched; generated schemas: zero.
- Final separate read-only check: production hashes matched the persisted
  pre-cleanup baseline; generated test schemas: **zero**. The existing manual-test
  schema remained present (one), preserving the synthetic browser accounts.

### Current outcome

All **118 distinct collected tests have passing results** across these bounded
runs. There were 120 successful test executions because the two integrity cases
were repeated in the third batch. No tests were skipped. The intermediate setup
error remains documented; this is not a claim that one uninterrupted 118-case
process completed without error. No assertions, TLS requirements, project guards
or group protocols were weakened.

The original failed full runs and the interrupted third batch could not complete
their post-run production snapshots. That verification gap is preserved in the
record, rather than retroactively claimed as successful. All completed-batch
comparisons and the final saved-baseline comparison matched; no production write
was performed by any run. Cleanup is now verified, not merely assumed.

The three logged constraint SQLSTATEs are expected, caught integrity checks.
The separate connection failure is now identified as client TCP **connection
refused**, SQLSTATE None, during connection establishment before SQL. It also
prevented the same process from opening a production read-only snapshot, despite
the projects using different hostnames. A separate process continued its held
and fresh test-project connections. This suggests an intermittent pooler/network/
local-egress path problem, but does not distinguish among them. It does not prove
that Supabase was down, that connection limits were reached, or that the issue
has been repaired. No application connection leak was observed in these runs.
Pooler acceptance logs and local-egress evidence at the exact refusal time are
needed for definitive attribution. The six-minute read-only probe passed but
cannot guarantee future uninterrupted connectivity.

No further test retry is scheduled automatically. No application feature,
production record, approved scenario, credential, configuration, version, commit
or tag was changed during this investigation. Release version remains 0.5.0.

The historical single-process failed runs above remain part of the record.
Successful bounded batches do not identify or repair the original connection
interruption. No production fallback, TLS changes, credential changes, application
behavior changes, commits, pushes or version changes were made during this
SQLSTATE investigation.

## Final revision-2 browser-review validation

The approved scenario files and production schema/history remain unchanged.
Revision 2 is stored in `data/scenario_realism_drafts.json` and loaded only by
the explicit disposable-project review launcher. No normal application route
automatically substitutes drafts. See SCENARIO_REALISM.md for evidence changes,
priority reapproval cases, browser instructions and the history-freezing policy.

Current **127 distinct cases passed**, no skips, across bounded batches:

| Batch | Result | Duration |
|---|---|---|
| New corpus workflows + performance + target guards | 22 passed | 80.21s |
| Adaptation, fixed control, presentation and original-source integrity | 50 passed | 134.77s |
| Database operations and matched-pair workflows | 18 passed | 104.51s |
| Security, mistakes and current review-loader/workflows | 42 passed | 82.51s |
| Final easy-message refinements and strengthened corpus/loader/workflow checks | 9 passed | 42.62s |

Batches overlap; totals are successful executions, not additional distinct cases.
The final nine-case run validates the latest body refinements and schema-qualified
loader. An initial newsletter-length check failed before database tests; the
draft was corrected and the current checks passed. No outstanding assertion
failures or connection errors occurred in the final batches. No tests were skipped.
Each completed database batch reported matching production hashes, no open test
connections and zero generated automated test schemas.

Both revised-corpus groups complete ten sequential responses. The experimental
strong-performance branch receives five distinct hard scenarios after five
intermediate responses. The control receives its fixed schedule despite poor
performance. Pair safety, reasoning, confidence, elapsed time, educational
feedback, completion and results are preserved. Missing/wrong target, public
schema, missing TLS, nonempty targets and protected-metadata edits are rejected.

Chrome hostile-content/inspection safety passed. A live Chrome check also
verified all 27 revised cards, visible context, the repaired invoice evidence,
final easy-message refinements, and no external hrefs or placeholder bodies.
The final live review is http://127.0.0.1:5006/review. New synthetic workflow
credentials are stored outside Git in a local permission-0600 file.

Final test-project inventory: zero `phishsense_test_*` schemas, one intentionally
retained `phishsense_review_*` schema for the requested browser review, and the
existing manual-test schema retained. The first review copy was gracefully
refreshed only to include the finalized easy-message text; the normal app and
existing manual sandbox were not restarted/reset. No participant records were
copied into or edited by this sandbox.

### Production-preservation detail

Every before/after production hash comparison for this work matched. A separate
comparison with an older saved baseline initially differed by one session, ten
responses and two evaluations. Read-only prefix-hash verification showed **every
older row in all five production tables still matched exactly**. The additional
completed session predates revision preparation. Thus the older-baseline
difference is pre-existing append-only activity, not evidence that this refinement
rewrote participant history. No identities, answers, password hashes or
participant details were printed. Production users and scenarios match the older
baseline in full.

The earlier TCP-refusal cause remains unproven; these successful bounded batches
do not establish a provider/network repair. No production writes, import, schema
migration, credentials/configuration changes, research-rule changes, commit, push,
tag or version change were performed. Version remains 0.5.0. Participant-use
approval and immutable content-version planning are still required before any
production activation.

## Third review revision

Revision 3 updates all 27 draft stimuli, neutralizes context, varies genres,
corrects mechanism metadata, adds equivalent safe Reply-To/permission inspection,
and replaces participant item IDs with opaque references. See
[SCENARIO_QC_REVISION3.md](SCENARIO_QC_REVISION3.md) and
`data/scenario_qc_revision3.json` for the full reviewer-only audit. The original
approved corpus, labels, objectives, research rules and production data remain
unchanged. Browser review is isolated at http://127.0.0.1:5007/review, preserving
the revision-2 snapshot at port 5006. No stimulus is activated for participants.

All 133 distinct cases passed across bounded batches (24/57/18/34), no skips;
the final legacy action was independently rechecked (1 passed). Completed-batch
production hashes matched and automated test schemas reached zero. Chrome
hostile-content and live-review checks passed. Empirical ratings, pair-level
evidence approval and immutable production content/versioning remain pending.
No version bump, commit, push or production migration occurred.

## Final targeted content pass

See [SCENARIO_FINAL_REFINEMENT.md](SCENARIO_FINAL_REFINEMENT.md) and
`data/scenario_qc_final.json` for the complete final report. Six proposals changed;
21, including all eight foundation scenarios, are unchanged from archived
revision 3. IDs, labels, objectives, pair keys, provenance and all training rules
remain unchanged. Review copy: http://127.0.0.1:5008/review.

All 137 distinct tests have passing results across bounded/resumed runs, no skips.
One intermediate matched-pair attempt had a TCP-refused test failure and teardown
error; exact-fixture cleanup and resumption passed the five incomplete cases.
No assertion failure remains. Final production hashes match the pass baseline;
zero automated schemas remain. Three browser review schemas are intentionally
retained alongside the existing manual schema. Chrome safety/live checks passed.

A separate read-only methodological audit found that the preserved control
selector chooses 9 phishing / 1 legitimate, including an all-phishing baseline.
This was not changed. It needs explicit research-design approval before study
use; the global corpus is still 13/14 and the difficulty schedule is correct.
Thus automated functional coverage is complete, but participant-readiness and
final study sign-off are not established by those tests. Empirical calibration,
final evidence approval, immutable content activation and the intermittent
TCP-refusal investigation remain documented review/operational items.
No commit, push, tag, production update or version bump occurred.

## Final cleanup and requirement checklist

The SD-4926 capitalization correction, targeted difficulty/mechanism reviews,
latest validation results, manual browser checklist and unresolved study/operational
concerns are recorded in [MILESTONE6_STATUS.md](MILESTONE6_STATUS.md). No labels,
protocols, production records or application release identifiers changed.

## Approved balanced-selection protocol (latest local implementation)

The user approved 5P/5L sessions on November 22, 2026. New sessions now use
`rules-v4-balanced-selection`, with a 2P/3L intermediate baseline and 3P/2L
remainder. Fixed control difficulty order, experimental thresholds, pair exclusion
and older protocol behavior are preserved. No migration or historical conversion
is used. See [BALANCED_SELECTION.md](BALANCED_SELECTION.md) for exact changes,
all 22 new passing tests and the latest partial regression results: 126 distinct
passes, one infrastructure-blocked case, 32 database cases not rerun, zero skips.
Full Milestone 6 sign-off remains blocked by intermittent connection refusal.
The fresh diagnostic confirmed no automated schemas remain. Production was not
accessed; no release or Git action occurred.
