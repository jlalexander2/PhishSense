# PhishSense testing — Milestone 6 development

Install the application requirements and configure credentials locally using
`.env.example`. The example contains placeholders only; actual environment files,
certificates, databases and local recording credentials are not committed.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

The current development suite contains **137 tests** (the released Milestone 5 suite contained 69). Without TEST_DATABASE_URL, database tests
explicitly skip; those skips do not demonstrate successful Supabase validation.
Set TEST_DATABASE_URL locally to a disposable Supabase development database or an
authorized test target in a different Supabase project from DATABASE_URL. The runner
and fixtures reject production fallback and unverifiable project identities. TLS uses verify-full and the configured trusted CA.

Database fixtures create unique phishsense_test_* schemas and synthetic records,
then remove their schemas. They do not use real accounts or public training
records. Test login passwords and Flask signing keys are generated at runtime,
not published reusable credentials. Do not point a schema-creation test role at
an unapproved database.

Coverage includes registration/login, password hashes, PostgreSQL constraints and
rollback, read-only SQLite migration, scenario import validation/idempotency,
ordered ten-email workflows, feedback, reasoning/confidence/timing/progress,
adaptive threshold boundaries, fixed control scheduling, matched-pair exclusion,
hard-pool capacity, legacy protocol protection, recurring errors, exact metadata
associations, learner isolation and read-only summary access.

Browser validation completed high/low experimental and high/low control profiles
and verified the new mistake summary. Local browser launchers and recordings
are intentionally kept outside the submission because they contain demo login
information or machine-specific setup. These are optional and are not required
by pytest or the production application.

For release validation, run the complete suite once with the real PostgreSQL test
target, record failures/skips honestly, compare public application-table hashes
before/after, and verify temporary-schema cleanup. Stop on a connection failure;
do not weaken certificate verification or repeatedly retry. Historical pooler
refusals were intermittent; successful runs showed no connection leaks or backend
saturation, but their original cause was not conclusively established.

## Milestone 4 submission validation — November 10, 2026

The complete suite passed **52 tests, 0 failures, 0 skips** against Supabase in
149.68 seconds after replacing fixed test login secrets with runtime-generated
values. All five public application-table hashes remained unchanged. The run
reported zero connection failures and zero test connections left open. Previously
verified Chrome workflows cover both groups and the read-only mistake summary.
No production imports, migrations, group assignments or server restarts were
performed to prepare this submission.

## Milestone 5 release validation

Run `.venv/bin/python scripts/validate_milestone5.py` with an explicit separate
TEST_DATABASE_URL. The complete suite passed 69 tests with zero failures and zero
skips in 295.34 seconds on November 15, 2026. Production table hashes remained unchanged and all
generated test schemas were removed. Coverage additionally includes session
metrics, historical comparisons, atomic/idempotent completion, learner results,
reasoning escaping, access isolation, and protected next-session starts.

## Milestone 6 development validation

The suite now includes T25–T30 coverage for learner dashboard summaries, account
form CSRF, bounded and ambiguous inputs, inert hostile email content, signed
cookie handling, cross-learner access, and inventory fallbacks. Run the same
credential-safe validation runner shown above; it discovers all current tests.
The independent local-browser safety smoke check is
`.venv/bin/python scripts/verify_content_safety.py` (installed Chrome required).
See [MILESTONE6.md](MILESTONE6.md) for results and scope. Historical 69-test
Milestone 5 results above remain the evidence for the v0.5.0 release.

The November 22, 2026 Milestone 6 integration run stopped with 82 passed, one
connection-failed test and one connection error during teardown. Ten cases were
not reached. Final production hash comparison and generated-schema cleanup
could not be confirmed; no automatic database retry was attempted. This is not
a full-suite pass. See MILESTONE6.md before rerunning database validation.
The ten unreached offline cases subsequently passed separately (10 passed in
0.17 seconds), without database access. This gives 92 distinct passed cases across
the runs, with the single database workflow still blocked and cleanup unverified.

## Email realism refinement

The current suite includes 25 additional presentation cases (118 total): reserved
fictional destinations, inert inspectable links, escaped labels/attachments,
preserved warning evidence, context extraction, class/group/difficulty parity and
draft integrity. The earlier connection-blocked workflow subsequently passed in
a distinct disposable-project schema, with production hashes unchanged and zero
generated test schemas remaining. Full refinement regression validation remains blocked by a renewed connection
failure; see MILESTONE6.md for exact results.

Latest refinement run: 106 passed, one connection-failed test, one teardown
connection error in 289.54 seconds. Eleven cases were not reached. Ten offline
cases passed separately; the other unreached completion workflow passed targeted
validation earlier. There are 117 distinct successful current cases across runs,
with start-action validation still blocked. Final production hashes and cleanup
are unverified for this full run. Do not report 118 tests passed.

## Final resumed validation — November 22, 2026

All **118 distinct cases now have passing results**, with no skips, across bounded
runs: 19 passed (66.33s), 50 passed (142.42s), 36 passed before one setup connection
error (114.15s), then all 15 incomplete cases passed (36.29s) after an independent
verified read-only stability check and safe empty-fixture cleanup. Two integrity
cases were repeated, so there were 120 successful executions covering 118 cases.
This is not an uninterrupted single-process pass; the intermediate error is
retained in the record.

The setup error was TCP connection refused in psycopg.connect(), SQLSTATE None.
It is separate from the intentionally caught 23505/23514/23503 errors in the
negative integrity tests. The read-only probe passed for 365.78 seconds with 36
held and 36 fresh-connection checks. Observed test-process connection peaks were
one, with none left open. A definitive root cause of the intermittent refusal
remains unknown.

Final generated-schema count: zero; existing manual-test schema retained.
Completed-batch production hashes matched, as did the final saved cleanup-baseline
comparison. Failed processes could not complete their own final snapshots; this
gap is not retroactively claimed as verified. No production writes, TLS changes,
credential changes, application changes, commits or version updates were made
during the resumed investigation. Details: MILESTONE6.md.

## Revised-corpus browser review

The current suite contains 127 cases, adding nine checks for revision content,
isolated test-only loading, unchanged numeric IDs/metadata, nonempty-target
refusal, missing/wrong project and public/TLS guards, and full workflows against
the revised corpus. `SCENARIO_REALISM.md` describes the intentionally retained
review schema and separate reviewer browser address. Automatic test schemas
remain transient and are checked independently.

Revision-2 final result: all 127 distinct tests have passing evidence across
bounded runs (22/50/18/42, plus a nine-case final corpus rerun), no skips. Each
database batch reported matching production hashes and zero automated test
schemas. A separate browser-review schema is intentionally retained, and is
explicitly not an uncleaned automated-test fixture. Chrome hostile-content and
live-review checks passed. Original production rows match the saved older
baseline; additional activity predates revision preparation. Earlier network
refusals remain an unresolved operational history, not a failed current content
assertion. No production activation or release was performed.

## Third review revision

133 distinct current cases passed in bounded disposable-project batches:
24 (100.70s), 57 (142.53s), 18 (123.78s), 34 (49.72s), no skips. A strengthened
legacy fallback-form test passed separately (5.72s). All completed-batch
production hashes matched; automated test schemas and open observed test
connections were zero. New tests cover opaque references, server-side mapping,
raw-ID rejection, replay of a complete signed cookie, paired permission parity,
reviewer metadata omission, pool capacity and legacy row preservation. The old
workflow tests now use real opaque references rather than bypassing that guard.
Chrome security/live-review checks passed. See SCENARIO_QC_REVISION3.md.

## Final targeted refinement validation

137 distinct cases passed across bounded/resumed runs: 29 (107.30s), 57
(142.78s), 13 before one TCP-refused test plus teardown error (53.23s), five
incomplete cases resumed successfully (78.90s), and 33 (40.58s). No skips or
unresolved assertion failures. Final production hashes match the starting
baseline; automated test schemas are zero. Prior review/manual schemas remain
intentionally retained. Chrome safety and live review passed.

The final audit separately found 9/1 phishing/legitimate exposure in the current
control selection (5/0 baseline). This methodological issue is not a failed code
assertion and was not changed under a content-only refinement request. Explicit
approval is needed to balance predetermined items without altering the schedule
or rewriting existing sessions. See SCENARIO_FINAL_REFINEMENT.md.

## Balanced selection protocol (approved local Milestone 6 refinement)

New sessions use `rules-v4-balanced-selection`: 2P/3L intermediate baseline,
3P/2L remainder and 5P/5L overall. Control difficulty order and experimental
thresholds are unchanged. Old-protocol records/plans are not rebalanced. See
[BALANCED_SELECTION.md](BALANCED_SELECTION.md) for behavior and current results.
Earlier 137-case validation records above refer to earlier local builds.

The disposable-only runner also supports bounded test paths/node IDs:

```bash
.venv/bin/python scripts/validate_milestone6.py tests/test_balanced_selection.py
.venv/bin/python scripts/validate_milestone6.py tests/test_milestone6.py tests/test_mistakes.py
```

With no targets it discovers the complete suite. It requires explicit, distinct
TEST_DATABASE_URL, verifies disposable authentication/TLS before tests, guards
real connections against production routing, suppresses credential-bearing
tracebacks and stops at the first failure. It does not connect to production or
perform production hash comparisons. Cleanup checks compare generated schemas
against the starting set, preserving unrelated manual/review schemas. The test
fixture retains its schema-owner connection for cleanup instead of requiring a
new teardown handshake. There is no automatic reconnect/retry or TLS downgrade.

The current suite collects 159 cases, including 22 balanced-protocol cases.
Completed-run results are recorded in BALANCED_SELECTION.md; collection alone is
not a passing test result.

## Milestone 6 handoff checkpoint — November 22, 2026

Implementation substantially complete — final database regression testing and manual browser verification pending.

Current evidence: 126 distinct passes of 159 cases; one connection-blocked case,
32 database cases not rerun, zero reported assertion failures and zero skips.
Feature development and further tests are stopped at the user’s request.
See [MILESTONE6_HANDOFF.md](MILESTONE6_HANDOFF.md) before resuming verification.

## Local v0.6.0 packaging checks

Current local application metadata is v0.6.0; the latest published release remains
v0.5.0. This does not change selection-protocol identifiers or establish full
validation. The checkpoint remains 126 distinct passes, one connection-blocked
case and 32 database cases not rerun (159 collected; zero reported assertion
failures/skips). Packaging checks are offline only; see releases/v0.6.0.md.

Post-version-update offline validation: 105 passed, 54 database-dependent cases
deliberately deselected, zero skips (0.33s); compilation and whitespace checks
passed. No database case was rerun and no additional distinct suite passes are
claimed. Nothing was staged or committed during preparation.
