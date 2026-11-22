# Milestone 6 handoff

**Status: Implementation substantially complete — final database regression testing and manual browser verification pending.**

Checkpoint: November 22, 2026. Feature development is stopped at the user's
request. Preserve the current uncommitted local implementation. Local build
version is **v0.6.0**; the latest published version remains **v0.5.0**. The
selection protocol remains **rules-v4-balanced-selection**. Local commit
preparation is authorized; staging and committing await separate user approval.
No v0.6.0 tag or release has been created.
No further feature, scenario, database or release changes are authorized by
this checkpoint. This handoff does not establish final validation or study readiness.

## T25–T30 checklist

| Requirement | Implementation preserved locally | Test/verification evidence and remaining work |
|---|---|---|
| T25 Dashboard progress summaries | Learner-owned completed-session totals, weighted accuracy, time, confidence, latest results and change; incomplete sessions excluded; empty states; read-only calculations | Previously exercised by dashboard/database tests. Latest complete database regression rerun is pending. Verify layout, empty/partial/completed views and navigation manually. |
| T26 Input and simulated-content safety | Required and bounded inputs; duplicate-field rejection; parameterized queries; HTML escaping; restrictive security headers; inert link, attachment, Reply-To and permission inspection | Offline safety/content cases passed; Chrome hostile-content smoke check passed with zero unsafe-resource requests. Prior all-27 rendering evidence exists; latest database-backed rendering rerun is pending. Verify interactive inspection/accessibility manually. |
| T27 Classification and feedback workflow | Ordered ten-response sessions; classification, reasoning, confidence, elapsed time and actual difficulty recorded; immediate feedback, progress and atomic completion; replay/skip rejection | New full workflows passed for all three experimental outcomes and good/poor control performance, with metrics/scoring assertions. Remaining original workflow/results regressions are pending. Complete manual synthetic browser walkthroughs. |
| T28 Adaptive progression and fallback | Original five-response evaluator/thresholds; balanced feasible selection; pair exclusions; insufficient-data behavior; blocked infeasible creation; balanced retained plan when target inventory becomes unavailable | New tests passed all three adaptive paths, capacity/pair rejection and synthetic inventory-loss fallback. Existing adaptive regression cases passed before interruption. Demonstrate decision timing and fallback manually. |
| T29 Authentication, isolation and sessions | Existing hashed-password authentication; protected account/logout forms; session rotation, cookie flags, ownership filters and opaque scenario references | Offline authentication/input/tampering checks passed; older integration evidence exists. Latest database-backed authentication/isolation regressions remain pending. Verify two-browser isolation, logout/back/reload and stale forms manually. |
| T30 Database integrity and group separation | Explicit disposable-only test routing; verified TLS; isolated schema fixtures; deterministic fixed control plan; versioned new-session balance; old plans/results preserved | All 22 new balanced-protocol cases passed, including both groups, pair exclusions and historical preservation. Full database regression remains blocked by connectivity. Latest read-only cleanup check found zero automated test schemas. |

“Previously exercised” refers to earlier recorded validation, not a claim that
those database cases passed again after the latest selector changes.

## Exact current test status

**159 collected cases: 126 distinct passes, 1 connection-blocked case,
32 database regression cases not rerun. Zero reported assertion failures,
zero skips. The current suite has not passed in full.**

- All **22 new balanced-selection tests** have passing evidence.
- The complete offline subset passed **105 cases**; 54 database-dependent cases
  were deliberately deselected. Deselection is not a skip or a database pass.
- The interrupted regression batch passed **24 cases**, then stopped on
  `tests/test_control_schedule.py::test_fixed_control_sequence_ignores_all_performance`.
- These runs overlap; do not add their counts. Detailed run totals/durations and
  overlap accounting are in [BALANCED_SELECTION.md](BALANCED_SELECTION.md).
- Chrome hostile-content, compilation and whitespace checks passed.
- Latest fresh read-only check: **0 automated test schemas**, with **3 review
  schemas and 1 manual-testing schema** intentionally preserved.
- Older 137-case passing evidence belongs to earlier local builds; it does not
  replace the remaining validation for the current 159-case build.

No tests or database connections were attempted while preparing this handoff.

## Balanced protocol and preservation

Only newly created sessions use `rules-v4-balanced-selection`:

- Ten distinct items: **5 phishing / 5 legitimate**.
- First five: intermediate, **2 phishing / 3 legitimate**.
- Remaining five: **3 phishing / 2 legitimate**.
- Control difficulties: **I,I,I,I,I,E,H,I,E,H**, with the full deterministic plan
  saved before training and independent of performance/history.
- Experimental difficulty: unchanged five-response thresholds; creation verifies
  feasibility of easier, intermediate and advanced continuations.
- Quotas/future labels remain absent from participant-facing content. Opaque
  references, server ordering and matched-pair exclusions remain intact.

Existing v1/v2/v3 plans, responses and completed results are not converted or
rebalanced. Older saved sessions can resume under their stored protocol. The
existing algorithm_version field distinguishes versions for later analysis;
scoring formulas and group assignments are unchanged. No schema migration is
needed. Historical controls may still contain the earlier 9/1 mix and must not
be treated as balanced-v4 exposure.

All 27 scenario IDs, labels, difficulty assignments, provenance and three pairs
remain preserved. The refined corpus remains local review content; no production
replacement/import occurred. The hard pool supports five pair-safe items with no
spare capacity. Empirical calibration and safe content-version activation remain
separate study-readiness considerations, not reasons to restart feature work.

## Manual browser verification still pending

Use synthetic accounts in a **fresh verified disposable-only process**, not the
normal production-connected application. Do not run these steps now.

1. Check login, protected-route redirects, logout confirmation and two separate
   browser profiles for experimental/control learner isolation.
2. Inspect the Evercrest inbox and training screens. Check mouse/keyboard link
   inspection, exact apparent destinations, Reply-To, permissions and attachment
   previews. Confirm no external navigation/download/resource execution and no
   pre-answer source IDs, ratings, reviewer notes, quotas or answer keys.
3. Submit classification, nonblank reasoning and confidence; verify immediate
   feedback, saved reasoning and progress. Try skipped/stale submissions, double
   submission, back and reload without duplicate responses.
4. Demonstrate an experimental decision only after response five. Automated
   coverage already exercises all three paths; manually inspect decision evidence
   and the actual presented continuation, not just a displayed difficulty value.
5. Complete a control session; compare good/poor synthetic outcomes without
   changing its stored difficulty sequence or item plan. Inspect balance only in
   reviewer/server evidence, without adding participant hints.
6. Confirm ten ordered responses, no matched pair together, complete results,
   training history and dashboard statistics. Check empty and partial history too.
7. Check old/new protocol distinction and preservation in synthetic fixtures.
   Never use real historical participant records as editable demonstration data.

Older running review processes may retain older imported code and snapshots.
Existing ports/credentials are not assumed current; verify the disposable target
and launcher before a future browser session. Do not reset old sandboxes.

## Intermittent connection refusal

The latest blocked case failed while opening a connection at test line 119,
**before SQL**: OperationalError, SQLSTATE None, category “connection refused”.
No application assertion or teardown error was reported. The runner's subsequent
fresh cleanup-check connection also refused. Database tests stopped without retry.

A separate read-only process subsequently authenticated with verified TLS. DNS
resolved three addresses; configuration used the session-pooler hostname/5432
port. PostgreSQL activity was 15/60 connections. That is not the pooler client
limit and does not prove pooler health. Root cause remains unresolved. Expected
unique/check/foreign-key errors from negative integrity tests are unrelated to
this TCP-level failure. Holding each test's owner connection improved cleanup,
but did not resolve connection establishment failures.

Recommended investigation **when verification resumes**, without changing secrets
or weakening TLS:

1. Recheck distinct TEST identity, configured session-pooler endpoint/port and
   certificate verification before any schema-creating test.
2. Correlate timestamped refusal categories with disposable-project pooler logs,
   maintenance/status events and actual pooler client/backend limits. Distinguish
   those from PostgreSQL max_connections and deliberate constraint-test errors.
3. Check DNS/address reachability and local network/VPN/firewall behavior during
   the failure window. Keep endpoint details and credentials out of shared logs.
4. Inspect connection lifecycle and observed concurrency; use bounded sequential
   batches. Do not diagnose exhaustion from cumulative connection counts alone,
   blindly retry, alter credentials, disable verification or use production.
5. If still unexplained, provide Supabase support sanitized timestamps/error
   categories and connectivity observations through the project's normal support
   process; no support message has been sent.

## Safe resume point

When the user requests resumption: review Git status and this handoff, verify the
disposable target, then use `scripts/validate_milestone6.py` for bounded validation.
It requires explicit TEST_DATABASE_URL, guards actual connections to TEST,
stops on failure and does not query production hashes. Resume the blocked case
and outstanding database groups (control, integrity, matched pairs,
security/isolation, rendering and performance). After successful regression,
verify own-schema cleanup and complete the browser checklist. Keep historical
run failures visible in the record. Do not claim sign-off from passing counts
alone; record any failures/skips and remaining manual work.

Implementation/validation did not access production; a fresh production hash
comparison was deliberately not performed. Existing uncommitted work is retained.
No commit, push, tag, deployment, version change, production edit or new feature
is part of this handoff. Future researcher analytics/administration, hosting
hardening and corpus expansion require separate scope/approval.

## Subsequent manual check: static attachments and corpus routing

Attachment inspection was explicitly deferred to Milestone 7; retain the static
Milestone 6 tiles. See
[MILESTONE6_ATTACHMENT_CORPUS_VERIFICATION.md](MILESTONE6_ATTACHMENT_CORPUS_VERIFICATION.md)
for the database-free safety evidence, normal-app versus retained-review corpus
routing, current offline preview and the approval boundary for a fresh disposable
workflow review. No activation or database write was performed. The planned
accessibility/safe-rendering/inertness requirements are in
[MILESTONE7_ATTACHMENT_INSPECTION_PLAN.md](MILESTONE7_ATTACHMENT_INSPECTION_PLAN.md);
this is documentation only, not the start of Milestone 7 implementation.

## Local version preparation

VERSION and current-build documentation now identify v0.6.0, consistent with
previous milestone numbering. This metadata update does not change training
protocols or the pending-verification status. Historical v0.4.0/v0.5.0 release
notes and earlier validation records remain unchanged. Commit scope is awaiting
user review; nothing is staged, committed, tagged, pushed or deployed by this
preparation. Only offline checks are permitted for this packaging step.
