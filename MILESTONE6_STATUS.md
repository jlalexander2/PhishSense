# Milestone 6 verification status before balanced-protocol implementation

For the subsequently approved local v4 selector and latest validation, see
[BALANCED_SELECTION.md](BALANCED_SELECTION.md). The record below documents the
pre-v4 verification and its operational interruption.

Local review only. Version remains 0.5.0. No commit, push, release, deployment,
production import, schema migration, or research-protocol change is authorized by
this review. Earlier validation records remain historical evidence; the latest
results below supersede their status, not their recorded failures.

## Final copy cleanup and scenario review

Only `evercrest-adv-draft-legit-003` was edited in this cleanup: “For SD-4926,
When…” became “For SD-4926, when…”. The preservation test allows exactly that
capitalization correction to the previously unchanged foundation scenario.
No evidence, answer, mechanism, learning objective or rating was changed.

- `legit-003`: order, item, portal and reception-task comparisons are available.
  Routine fulfillment may be an easy/intermediate boundary; retain intermediate
  pending pilot review and explicit approval of any relabeling.
- `phish-0003`: the zero in the lookalike domain is defensible evidence, but one
  comparison may be sufficient. Retain intermediate pending the same review.
- `phish-0055` and `phish-0002`: retain both. Delivery and invoice contexts support
  transfer practice, but both use executable-as-document deception and represent
  one mechanism family, not two distinct mechanisms.

| Retained difficulty | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy / beginner | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Advanced | 4 | 4 | 8 |
| Total | 13 | 14 | 27 |

All 27 source IDs, classifications, difficulty labels, source hashes, provenance,
objectives and pair relationships remain protected. Three advanced pairs and two
independent advanced scenarios permit exactly five distinct pair-safe advanced
items; there is no spare advanced capacity. Twelve intermediate items support
baseline planning; relabeling requires pool-capacity review first.

Across the proposed email bodies, legitimate word counts are 54–119 (median 78),
and phishing counts are 60–128 (median 71), counting the presentation markup as
text. Both classes contain links and attachments and share the same renderer.
These descriptive checks support comparable presentation, not proof of equal
empirical difficulty. Neutral workplace records retain relevant facts without
explicit classification/rule statements. Residual cues include the two easy
executable cases, concentrated executive-payment phishing, and domain-comparison
boundary cases. No claim of zero statistical or human-perceived clues is made.

The refreshed offline reviewer page is
`/private/tmp/PHISHSENSE_FINAL_REVIEW.html`. It deliberately includes answers and
must not be given to participants. Existing running review servers retain their
previous database snapshots; this cleanup does not overwrite their scenarios or
synthetic histories. A fresh launch is needed to view the capitalization change
through a running review server. Normal application `/review` is unavailable.

## T25–T30 checklist

| Requirement | Implemented and covered by automated tests | Manual verification still needed |
|---|---|---|
| T25 Dashboard summaries | Authenticated learner-only completed-session totals, weighted accuracy, time, confidence, latest result and change; partial sessions excluded; empty state; no GET writes | Intended browser layout, navigation and readability with empty/partial/completed history |
| T26 Input/content safety | Bounded and unambiguous forms; required reasoning/confidence; finite timing; parameterized queries; escaping; restrictive CSP and headers; inert link/attachment/permission inspection; all-27 rendering checks | Mouse, keyboard and touch inspection; Reply-To/permissions readable; no confusing navigation affordances |
| T27 Classification/feedback | Ten ordered responses; correctness, reasoning, confidence, time and actual difficulty stored; immediate feedback; progress and atomic completion; stale/replay/skip rejection | One complete synthetic session, feedback and results navigation, back/reload behavior |
| T28 Adaptive/fallback | Five-response block decisions, approved thresholds and boundaries; pair exclusion; insufficient-data and inventory fallback; unavailable control schedule blocks rather than substitutes | Demonstrate a recorded adaptive decision and a blocked/fallback state using disposable synthetic data |
| T29 Authentication/isolation | Hashed password verification, protected account/logout forms, session rotation, cookie flags, tampering rejection, own-learner training/results/history/mistakes filters | Two-browser learner separation, logout/back behavior and intended HTTPS configuration when hosting |
| T30 Database/group integrity | Explicit distinct disposable target, verified TLS, schema-scoped fixtures, constraints, both full workflows, fixed control difficulty independence and record-preservation checks | Study-design approval of exposure balance; participant-readiness review; operational connection stability |

Participant scenario identifiers are opaque HMAC references bound to learner,
session, nonce and the stored server plan. Raw scenario IDs are rejected in POSTs,
numeric GETs do not expose a scenario, and plan/active numeric IDs are removed
before cookie serialization. Results retain a session identifier with server-side
ownership checks; this is not a scenario answer key. Reviewer fields, source IDs,
ratings and answers are excluded from pre-classification training templates.
Correct answers and explanations remain intentionally visible after submission.

## Validation

Latest bounded validation: 29 passed (112.63s), then 57 passed (143.21s).
The database/matched-pair batch stopped with 13 passed, 1 connection-failed case
and 1 teardown error (60.38s). A separate offline security/recurrence selection
passed 23 cases (0.14s), with no database access. **122 distinct cases passed;
1 is connection-blocked; 14 were not rerun; zero skips were reported.** There is
no current complete 137-case pass. The older 137-case evidence remains historical.

The failed experimental matched-pair case raised OperationalError, SQLSTATE None,
category connection refused, inside psycopg.connect before SQL. A fresh read-only
check resolved three test endpoint addresses, authenticated with verified TLS,
and observed 15/60 PostgreSQL connections. The production read-only check also
refused connection, so the final production hash comparison is unavailable.
The first two completed batches verified matching production hashes; no production
write/schema operation was executed in this work. Do not equate that fact with a
successful final post-failure snapshot.

Exactly one newly generated test schema remained. It was positively matched to
the failed synthetic experimental fixture (1 user, 27 scenarios, 1 session,
7 responses and 1 evaluation), then removed after re-verifying its table counts
in the disposable project. Three intentional review schemas and one manual
schema were preserved. No tests were retried after recurrence. The remaining
database-backed authentication/isolation/fallback and matched-pair cases await
restored connectivity; offline security checks passed. Integration tests use only the
verified disposable TEST_DATABASE_URL, with no production fallback. Production
access is restricted to read-only before/after hashes of the five application
tables. Test fixtures remove only their own generated namespaces. Intentional
browser-review and manual-testing namespaces are preserved.

Chrome hostile-content smoke check passed: escaped injected HTML, no executable
script/frame/image and zero attempted injected-resource requests. It does not
replace interactive browser verification. Collection finds 137 cases; local
copy-preservation checks passed (3 cases, 1 database case deselected in that
preliminary command, not skipped). `git diff --check` passed.

## Unresolved issues and sign-off boundaries

1. **Research-comparison concern:** the preserved deterministic control selector,
   using current scenario IDs, yields 9 phishing / 1 legitimate, including five
   phishing baseline items. Difficulty order and non-adaptive behavior are
   correct, but global 13/14 balance does not ensure balanced exposure. Any
   balanced predetermined item schedule needs explicit protocol approval; this
   review does not change selection or historical plans.
2. **Operational concern:** previous TCP connection refusals occurred before SQL,
   sometimes during fixture teardown. Root cause remains unproven. Expected
   duplicate/check/foreign-key violations in negative tests are unrelated and
   handled by rollback. PostgreSQL activity below its limit does not establish
   the pooler's client limit. Passing bounded runs does not prove the intermittent
   problem is resolved; stop on a recurrence rather than repeatedly retrying.
3. **Content activation:** revised stimuli remain local review candidates.
   Production still uses its existing corpus. Approval and immutable content
   version/snapshot planning are needed before activating revised research
   stimuli, so historical results cannot acquire changed stimulus content through
   joins. No in-place production replacement is part of this work.
4. **Calibration:** human/pilot review remains necessary; no automated test proves
   an authored difficulty rating. The two flagged labels are unchanged.

Milestone 6 implementation coverage can be assessed separately from study and
deployment readiness. Do not declare final study sign-off while these concerns
remain. No new application feature was introduced by this cleanup.

## Future work outside this review

Researcher analytics/exports and administration require separately scoped work.
Deployment-level rate limiting, account recovery/email ownership verification,
centralized session revocation, HTTPS hosting and a restricted backend role also
need their own deployment plan. Signed-cookie logout clears the browser cookie;
it does not revoke an already copied cookie centrally. None of those features
was added here, and no additional research protocol was invented.

## Subsequent selection audit

See [SCENARIO_SELECTION_BALANCE_AUDIT.md](SCENARIO_SELECTION_BALANCE_AUDIT.md)
for the requested 50/50 feasibility proposal. No selector change is implemented
and all protocol changes await explicit approval.
