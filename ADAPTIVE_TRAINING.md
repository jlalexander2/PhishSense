# T14/T15: baseline selection and difficulty evaluation

The user approved these rules before implementation. This is a transparent
heuristic for the capstone prototype, not a validated psychological measure.
No random research-group assignment, recruitment, assessment protocol, or group
sizes were introduced or changed.

## Levels, baseline, and groups

Database labels remain `beginner` (easy), `intermediate`, and `advanced` (hard).
Every new training session starts at intermediate. Existing sessions and
responses are preserved as historical records, with NULL algorithm version;
they are not retroactively adapted.

`users.study_group` is explicitly `unassigned`, `control`, or `experimental`.
Existing and newly registered accounts default to `unassigned`, which receives
non-adaptive intermediate training. No account is automatically enrolled in the
experimental group. Group assignment is a researcher-controlled database action
under the approved study protocol, not a learner-selectable form field.
A session snapshots the group and algorithm/protocol version at creation. Changing an account's
group affects only future sessions, preserving the interpretation of existing
responses. Historical sessions remain unassigned rather than inferring their
research treatment.

## Approved decisions

Evaluate each non-overlapping block of five completed responses within a new
session, at the current level. No adjustment occurs after one to four responses.

| Decision | Conditions across the five responses |
|---|---|
| Increase one level | Accuracy >=80%, median response time <=60 seconds, mean confidence >=4 |
| Decrease one level | Accuracy <60% |
| Decrease one level | Accuracy =60%, median response time >90 seconds, mean confidence <=2 |
| Maintain | Otherwise |

Difficulty is clamped to the three levels. Control and unassigned groups never
receive performance-based changes, regardless of their metrics. Mixed-level
blocks are recorded without adjustment as a defensive compatibility safeguard.
At a ten-response session boundary the second block is recorded, but its
result does not override the intermediate baseline of the next new session.

Response time is elapsed wall-clock time from opening an email to submitting it,
including time in other tabs, as in Milestone 3. It is not a direct reading-speed
measurement. Raw times, reasoning and confidence remain stored unchanged.

## Selection and availability

For experimental and unassigned sessions, at the requested level, prefer scenarios the learner has never answered in any
session. Only after unused scenarios are exhausted, reuse previously completed
scenarios, oldest last-completion time first. Randomize ties. Never include the
same scenario twice in a session; reviewed scenario IDs remain excluded.

At an applied level change, keep the reviewed inbox rows and replace only the
unanswered rows. The ten-email total and recorded responses stay intact. If the
target level has no scenarios, retain the current level and record the availability
fallback. Also retain the current level if it cannot fill all remaining inbox
slots without duplicating a reviewed scenario; this preserves session length.
At the final block, a target level must still have an eligible scenario before
being recorded as applied. Unanswered scenario reservations do not count as
completed and can therefore be replaced.

At the initial T14/T15 inspection, inventory was 7 easy, 12 intermediate,
0 hard, so promotion was blocked by availability. The later approved advanced
import is described in SCENARIO_INTEGRATION.md.
No scenarios were relabeled, created, or approved by this implementation.

## Data and transactional behavior

`training_sessions.scenario_ids` persists each new inbox selection as JSONB;
the signed browser session is refreshed from it. `difficulty_evaluations` stores
block number, exact response IDs, group/version, accuracy, median time, mean
confidence, previous/proposed/applied levels, reason and timestamp. Existing
`training_responses` fields retain the actual presented difficulty and raw data.

Training submissions lock their session row before duplicate checking. Response,
evaluation and replacement selection commit together. A unique session/block
constraint and repeated-block check prevent duplicate evaluations. Old browser
tabs cannot submit scenarios replaced by an adaptive decision.

## Schema and verification

For existing installations, run `python scripts/apply_adaptive_schema.py --apply`
once after approval. The runner applies `migrations/004_adaptive_training.sql`
in one transaction and compares every pre-existing field before committing. It adds columns and one RLS-enabled table;
it does not drop tables or rewrite historic answers. Do not rerun `schema.sql`
on an existing database. Fresh installations use the full updated `schema.sql`.

Run `python -m pytest -q`. Real database tests need `TEST_DATABASE_URL` and use
isolated temporary schemas. Tests cover threshold boundaries, level bounds,
complete windows, control/unassigned behavior, baseline difficulty, adaptation
in the Flask workflow, non-overlapping blocks, persisted records, unused-scenario
priority, unavailable hard scenarios, and the original Milestone 3 workflow.


## Initial T14/T15 validation result

The approved additive migration was applied to the configured Supabase project.
All original fields were verified unchanged: 1 account, 19 scenarios, 4 sessions,
and 6 responses. Existing accounts remain unassigned and historical sessions
retain NULL algorithm versions. No learner was enrolled in an experimental group.

All **30 tests passed against Supabase** using temporary schemas and synthetic
data. Coverage includes the original workflow and adaptive/control workflows,
threshold boundaries, unavailable hard scenarios, persisted inbox recovery,
stale submission rejection, group snapshots, and oldest-first scenario reuse.
Restart Flask before using the updated implementation. Existing sessions finish
under their original behavior; new sessions use the intermediate baseline.

## Ordered mixed control protocol (supersedes the v1 control behavior)

New sessions now record `rules-v2-ordered-control`. Both groups must answer the
first five intermediate emails in their stored order. Only the next unanswered
email has an active inbox link. Later rows retain the Evercrest layout but show
Locked; direct GETs redirect to the inbox, and out-of-sequence POSTs are rejected
under the session row lock without inserting a response or evaluation.

The control schedule is fixed before training begins:

| Position | Difficulty |
|---|---|
| 1–5 | Intermediate |
| 6 | Easy (`beginner`) |
| 7 | Hard (`advanced`) |
| 8 | Intermediate |
| 9 | Easy (`beginner`) |
| 10 | Hard (`advanced`) |

Control IDs are selected deterministically by ascending scenario ID within each
level and persisted in `scenario_ids`. This selection queries no learner history,
accuracy, response time, confidence, reasoning, or mistake patterns. With an
unchanged approved inventory, control learners receive the same ten-scenario
sequence regardless of their prior or current performance. Unlike adaptive
selection, this fixed control sequence intentionally does not avoid scenarios
based on an individual's completion history. Repeated study sessions would reuse
this sequence; any multiple-session research protocol needs separate approval.

The control current difficulty follows the next scheduled email. Five-response
evaluation records still contain the same metrics, using reason
`fixed_control_schedule`; those metrics never determine control selection or
scheduled difficulty changes. The mixed second block does not invoke adaptive
rules. Experimental rules and thresholds remain unchanged.

Session creation requires six distinct intermediate, two easy, and two hard
scenarios. If any requirement is unmet, no control session or response is created:
the inbox shows a coordinator-facing availability message with HTTP 503. No
substitution or shortened schedule is allowed. At that implementation stage the
pool had 0 hard scenarios. The subsequent approved import added eight advanced
items with three matched-pair restrictions; see SCENARIO_INTEGRATION.md for
the current inventory and pair-compatible capacity.

No schema migration is needed: the existing version, group, ordered scenario IDs,
responses and evaluation fields store this protocol. Existing NULL-version and
`rules-v1` sessions keep their previous behavior and recorded results. They are
not silently converted to the ordered mixed protocol. Start a new session after
restarting Flask to use v2; this does not reassign any research groups.

Ordered-control validation: **35 tests passed against Supabase**, using isolated
schemas with synthetic data. This includes ten-response fixed-control completion,
identical sequences for contrasting performance profiles, blocking with zero or
one hard scenario, ordered GET/POST enforcement for both groups, and the original
registration/login/training/feedback/progress tests. No live research scenarios or
historical results were inserted, updated or deleted during this change.


## Current protocol: pair exclusion

New sessions now use `rules-v3-pair-exclusion`. All existing versions retain their
recorded selections and behavior. The approved eight-item advanced pool and its
metadata were imported through additive migration 005; older versions cannot
select that newly introduced content. Current hard selection enforces one member
per matched pair and retains both independent items when five hard emails are
needed. Control selection remains fixed and performance-independent. Details,
capacity limits and current validation are in SCENARIO_INTEGRATION.md.
