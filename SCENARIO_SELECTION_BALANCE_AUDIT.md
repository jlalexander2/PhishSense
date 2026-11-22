# Scenario selection balance — pre-implementation audit

The proposal below was subsequently approved November 22, 2026. Local
implementation and current validation are documented in BALANCED_SELECTION.md.
The audit is retained as the rationale; it is not the latest implementation status.

November 22, 2026. Read-only local audit of `adaptive.py`, session creation,
completion/scoring, research notes and the protected 27-item corpus. No selector,
research protocol, database, difficulty label or historical record was changed.
The control 9/1 result uses the earlier verified production-ID mapping, not a new
production connection. Pool calculations below are exhaustive local combinations.

## Current behavior

Control uses ascending scenario ID preference and a fixed difficulty schedule,
without classification quotas, learner history or performance inputs. The last
verified current-ID plan contains 9 phishing and 1 legitimate, with 5 phishing in
baseline. Adaptive selection prefers unused/oldest-completed items, randomizes
ties, enforces pairs, and also lacks classification quotas. Its initial ten-item
intermediate plan can contain 3–5 phishing. The first five can contain 0–5.
After a difficulty change the five easy items can contain 2–4 phishing; the five
pair-safe advanced items can contain 1–4. Thus feasible full-session phishing
ranges are 3–5 if maintained, 2–9 if demoted, and 1–9 if promoted. These are
structural possibilities, not observed participant frequencies or probabilities;
performance and prior exposures influence the actual path/order. The groups do
not currently have guaranteed comparable class exposure.

## Compatibility and feasibility

A five-phishing/five-legitimate quota is compatible with the implemented core
methodology: 15 learners per arm, five intermediate baseline responses, existing
five-response performance thresholds, fixed control difficulties, ten unique
items, feedback and pair exclusions. It is nevertheless a new selection/protocol
constraint, not a rule already documented as approved. Obtain explicit approval
and update research-method documentation before implementation/participant use.
It does not make the arms equivalent in difficulty, mechanisms or item identity.

| Pool | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Advanced | 4 | 4 | 8 |

All pairs are advanced, each with one of each classification. Five advanced items
require both independent items (one of each) and one member of each of three
pairs. Of eight valid five-item sets, three have 3 phishing/2 legitimate and three
have 2 phishing/3 legitimate. No additional scenario is needed for feasibility;
there remains no spare capacity for loss of an independent item or a pair family.

## Recommended constraint for approval

Use **2 phishing / 3 legitimate in the first five intermediate positions in both
arms**, then **3 phishing / 2 legitimate across the final five**. A five-item block
cannot be exactly 50/50. A consistent 3/2 baseline would also work; choosing one
shared composition is simpler than introducing unapproved counterbalancing.
Do not enforce a visible alternating label pattern or add a quota display.

After any particular 2P/3L intermediate baseline, exhaustive enumeration finds:

| Remaining difficulty path | Available valid 3P/2L continuation sets |
|---|---:|
| Experimental demotion: five easy | 12 |
| Experimental maintain: five unused intermediate | 6 |
| Experimental promotion: five advanced, pair-safe | 3 |

A 3P/2L baseline also permits all branches (6 easy, 10 intermediate, 3 advanced
sets with the complementary 2P/3L remainder). An arbitrary baseline does not:
a five-phishing baseline cannot reach 5/5 when either easy or hard items are
required. Baseline feasibility must be enforced before any response.

The control remains I,I,I,I,I,E,H,I,E,H. Its suffix can satisfy the same 3P/2L
quota without changing difficulty order or including both members of a pair.
A precomputed, approved balanced control item list should be stored before the
first response; it must not read accuracy, time, confidence, learner mistakes or
subsequent responses. Experimental difficulty alone remains performance-driven;
its classification remainder derives from assigned true labels, not learner
answers. Novelty remains a preference within feasible balanced sets, not a reason
to violate quota, pairs or difficulty. Cross-session reuse will still be needed,
especially for advanced items, under the existing reuse policy.

## Implementation implications — not implemented

- Create a new selection-protocol version for new sessions only; keep all v1/v2/v3
  dispatch and pair validation working. Simply replacing the VERSION constant
  would break explicit old-version checks and is insufficient.
- At creation, validate a balanced ten-item intermediate reservation plus a
  2P/3L baseline with all three future branches feasible. Store the control's
  complete fixed balanced plan immediately. Preserve current session locking and
  server ordering. Do not reinterpret in-progress older sessions.
- After response five, retain the approved evaluator unchanged; choose the
  remaining items using the target difficulty, complementary class quota,
  uniqueness and pair constraints in one transaction. Maintain must also preserve
  balance. Class quotas are not additional performance thresholds.
- Preflight all branches with current inventory. If later inventory changes make
  a target infeasible, retain a still-valid balanced current-difficulty plan under
  the existing unavailable-target behavior, recording the failure reason. If no
  valid ten-item plan exists, block creation/completion progression explicitly;
  never silently substitute difficulty, shorten the session or relax balance.
  The exact failure behavior should be approved with this proposal.
- The evaluator also runs at response ten. Keep that recorded decision's meaning
  distinct from item selection: no second-block response can be reassigned, and a
  completed session has no remaining class quota to fill. Preserve its existing
  difficulty-availability semantics unless separately approved.
- Current TEXT algorithm_version and JSONB scenario_ids can record the new
  protocol and plan; no schema migration appears necessary for this minimal
  approach. Add explicit tests for quota, all branches, control independence,
  scarce inventory, pair exclusion, history/reuse, old sessions and concurrent
  submissions. Do not change content in place while analyzing historical joins.

## Scoring, research interpretation and history

Correctness, accuracy, elapsed time, confidence, reasoning, recurring mistakes and
completion calculations need no formula change. The sample composition changes:
classifying everything as phishing can currently score 90% on the control plan;
with 5/5 it scores 50%. The same adaptive thresholds operate on a different,
controlled baseline mix, so promotion frequency may change without a threshold
change. A 2/3 baseline still weights the error types differently; applying the
same mix to both groups limits that particular between-arm confound.

Immediate feedback plus a known exact quota can let participants infer the final
answer by elimination; avoid adding participant quota hints and document this
limitation. Equal class counts alone do not balance mechanism, empirical item
quality or difficulty exposure. No extra counterbalancing or random assignment
scheme is proposed here.

No historical plan, outcome or evaluation should be rewritten or rebalanced.
Keep previous sessions under their stored protocol; resume them unchanged.
Separate pre-change synthetic/legacy sessions from new balanced-protocol research
analysis rather than pooling them as equivalent exposures. Existing study-group
assignments, account records and content provenance remain unchanged.

## Validation boundary

This proposal was checked with local exhaustive combinations, without database
access. It is not an implementation or an integration-test pass for a new
selector. Milestone 6 database validation separately stopped after another TCP
connection refusal: see MILESTONE6_STATUS.md. Approval of this proposal does not
resolve that operational blocker.
