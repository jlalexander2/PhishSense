# Milestone 6: balanced new-session selection

**Status: Implementation substantially complete — final database regression testing and manual browser verification pending.**

Feature development is stopped; see [MILESTONE6_HANDOFF.md](MILESTONE6_HANDOFF.md)
for the verification resume checklist.

Local application build: v0.6.0; selection protocol: rules-v4-balanced-selection.
Published release remains v0.5.0.

Approved November 22, 2026. Implemented locally; no production activation,
migration, import, published release or historical rewrite. The separately
authorized local build-version update does not change this protocol.

## Protocol

New training sessions store `rules-v4-balanced-selection` in the existing
`algorithm_version` field. Ten distinct scenarios must contain five phishing and
five legitimate. Positions 1–5 are intermediate with two phishing and three
legitimate; positions 6–10 contain three phishing and two legitimate. No quota,
answer schedule or classification metadata is sent to participant templates or
cookies. The existing opaque item references and ordered server validation remain.

Control plans are established at session creation using scenario-ID inventory
order, independent of learner history, accuracy, elapsed time, confidence and
mistakes. The difficulty sequence remains I,I,I,I,I,E,H,I,E,H. The complete stored
plan is unchanged during responses; only the displayed current difficulty and
ordinary fixed-schedule decision records advance.

Experimental creation reserves a balanced ten-intermediate plan and checks that
its fixed first-five baseline can support all three five-item continuation paths.
Candidate order prefers never-completed items, then oldest completed items, with
random ties, subject to all quotas, uniqueness and pair exclusions. Reuse across
sessions remains permitted when necessary. The existing five-response evaluator,
accuracy/time/confidence thresholds and boundaries are unchanged. At response
five, a difficulty change replaces only the unanswered suffix with a feasible
balanced target-difficulty suffix. Maintain retains the balanced reservation.

If inventory later becomes insufficient for the target, the existing valid
balanced plan is retained and the decision records `target_scenarios_unavailable`.
An infeasible initial inventory blocks session creation; no shorter session,
classification imbalance, pair relaxation or difficulty substitution is silently
introduced. At response ten no items are replaced: the existing one-item target
availability semantics for that recorded decision remain unchanged.

Server-side POST validation rejects a malformed new-protocol plan before saving
any response. Scoring and completion formulas are unchanged; stored response
labels/metrics still reflect actual presented scenarios and learner answers.

## Preservation and research interpretation

The v1/v2/v3 evaluators, ordering and v3 pair protections remain recognized.
Existing plans and records are not converted to v4. Explicit Start training can
resume an unfinished older saved plan instead of creating a replacement merely
because the latest protocol changed. Completed results remain under their stored
protocol. The existing TEXT/JSONB fields are sufficient; no schema change is used.

All 27 IDs, labels, difficulty assignments, provenance and three matched pairs
remain unchanged. Eight hard items support exactly five pair-safe selections;
both independent items and one member of each pair are required. For a 2P/3L
baseline, there are 12 easy, 6 remaining-intermediate and 3 advanced feasible
3P/2L continuation sets in the current corpus. No new scenario was authored.

Comparisons must distinguish v4 from earlier sessions; historical controls may
retain 9/1 exposure. Equal class totals do not prove equal empirical difficulty,
mechanism coverage or participant effort. Controlled baseline composition may
change promotion frequency despite unchanged thresholds. Immediate feedback and
a known exact quota may allow final-answer inference; no quota hint is added to
the participant interface. Earlier calibration/content-activation issues remain.

## Verification

`tests/test_balanced_selection.py` covers pure current-corpus feasibility,
determinism, unavailable inventory, pair exclusions, all three complete adaptive
paths, good/poor control outcomes, old-protocol preservation, and balanced fallback
after synthetic inventory loss. Existing regression fixtures now supply adequate
advanced inventory for new experimental sessions; historical evaluator tests
explicitly retain v3 rather than passing arbitrary legacy plans as v4.

Current verification covers **126 distinct passing cases out of 159 collected**.
There are zero reported assertion failures and zero skips. One database case is
infrastructure-blocked; 32 other database cases were not rerun after the stop.
This is not a complete 159-case pass.

| Run | Result |
|---|---|
| Initial balanced-protocol suite | 19 passed, 151.95s |
| Strengthened historical assertions and two added integrity/history cases | 5 passed, 35.92s; three overlap the initial run |
| Original advanced-package provenance regression | 1 passed, 0.09s |
| Adaptive/control/security-target regression batch | 24 passed, 1 connection-failed case, 132.57s; stopped |
| Entire offline subset, with actual DB connections prohibited | 105 passed, 54 database cases deselected, 0.34s |
| Chrome hostile-content check | Passed; zero unsafe-resource requests |
| Compilation and git diff whitespace checks | Passed |

All **22 new balanced-protocol cases** have passing evidence, including full
experimental decrease/maintain/increase and both control outcomes. Totals above
include overlaps; 126 is the distinct total, not their sum. The offline
*deselections* are intentional isolation, not skips or passing DB tests.

The blocked existing case is
`tests/test_control_schedule.py::test_fixed_control_sequence_ignores_all_performance`,
at line 119 while obtaining a connection for the next verification SELECT.
It raised OperationalError, SQLSTATE None, category connection refused, before
SQL. No application assertion or teardown error was reported. The runner's fresh
post-run cleanup check also refused connection; no database tests were retried.

One separate read-only diagnostic process then authenticated successfully with
verified TLS, resolved three endpoint addresses, confirmed the configured session
pooler hostname/5432 port, and observed 15/60 PostgreSQL connections. It confirmed
**zero automated test schemas**, preserving three review schemas and one manual
schema. The held schema-owner connection allowed fixture cleanup without a fresh
teardown handshake. This improves cleanup, but does not fix connection refusal.
The PostgreSQL count is not the pooler client limit; DNS success and an occasional
successful handshake do not prove endpoint reliability or provider configuration.
Root cause remains unproven. Prior expected unique/check/foreign-key violations
are handled negative tests, not evidence for this TCP-level failure.

The remaining database-backed security/isolation, matched-pair, content-rendering
and performance regressions require a successful new validation window. Review
browser behavior with synthetic accounts in a fresh disposable-only process after
connectivity is resolved; older running review processes retain their imported
code and snapshots. No server was restarted by this implementation.

No production connection, write, migration or schema change was performed during
this implementation/validation. A new production before/after hash comparison
was deliberately not performed; the connection guard blocks production entirely.
No credentials were printed, and `.env`, database TLS configuration, the canonical
schema, scenario content/provenance, performance formulas and VERSION were not
changed by this balanced-selection implementation.

The earlier control 9/1 audit remains valid for its historical v3 plan; it is not
the v4 behavior. Balance does not retroactively repair those sessions. Remaining
Milestone 6 sign-off items are infrastructure-blocked regression completion,
manual browser verification, final content activation/versioning review and
empirical calibration. Hard-pool expansion remains recommended before study use.

 Real connections in this run are
guarded to the verified disposable TEST project; production connections are
blocked. Test schema owner connections are held through teardown to avoid a fresh
cleanup handshake, with no retry or production fallback. Connection refusal is
reported as infrastructure failure separately from assertion failures. No claim
of provider stability is made from a successful test batch.
