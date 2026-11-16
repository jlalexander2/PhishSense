# Milestone 5: Performance Analytics and Session Results

Status: complete — v0.5.0 (Milestone 5). T20–T24 implemented and validated.
This work addresses the supplied T20–T24 outline. It does not add researcher
administration, exports, assessments or new experimental rules.

## T20 — Session performance calculations

`performance.py` derives classification accuracy, correct/response counts,
arithmetic mean elapsed response time, mean confidence and its 1–5 distribution,
and the same measures by actual `difficulty_at_response`. Empty denominators
produce unavailable values rather than a misleading 0% or 100%. Zero elapsed
seconds remain a valid measured value. Accuracy uses stored correctness.
Expected classifications in results are derived from stored correctness and the
submitted binary answer, rather than reinterpreting edited scenario labels.

Session-specific missed-phishing/false-alarm counts identify practice areas; the
existing cumulative mistake page and educational feedback remain unchanged.

## T21 — Historical performance

History retrieves only the authenticated learner's training sessions. Completed
sessions are ordered by completion timestamp and session ID. Aggregate response
accuracy/time/confidence are response-weighted, while average session accuracy
weights nonempty sessions equally. Latest-versus-previous accuracy is shown in
percentage points. In-progress sessions are listed separately and excluded from
comparisons. A legacy completed record with zero responses has no invented score.

Actual difficulty exposure is shown per session and across completed sessions.
Different scenario mixtures limit direct comparisons; this is descriptive learner
practice history, not a causal research analysis or a pre/post-test substitute.

## T22 — Completion

New responses are saved under the existing session row lock. On the tenth valid
response, completion is marked in the same transaction, before feedback renders.
The completion timestamp is idempotent and requires exactly ten unique response
scenario IDs matching the planned ten. A duplicate cannot substitute for a
missing planned response. Failed/rolled-back saves do not leave a completion mark.

Inbox/results/history GET requests do not backfill or update historical sessions.
Old unmarked sessions stay unmarked, including any legacy ten-response records;
there is no automatic migration of research history. Results require the recorded
completion timestamp to enter completed-session comparisons.

A POST-only, session-token-protected Start another session action serializes on
the learner row and reuses an existing unfinished current-protocol session instead
of creating duplicate sessions on repeated clicks. It does not alter group
assignment, baseline level, adaptive thresholds, ordering or pair exclusions.

## T23/T24 — Learner interfaces

- `/results`: latest completed session, or the current in-progress session when
  there is no completed one. An empty state is shown when neither exists.
- `/results?session_id=...`: one owned training session; foreign/missing IDs return
  404 and invalid IDs return 400. Incomplete sessions show an in-progress state.
- `/history`: completed-session comparisons and separately listed unfinished work.

Final feedback and the completed inbox link directly to results. Learners can
start another session after completion. Existing dashboard links now lead to
functional pages. New pages match the existing navy/teal theme, escape reasoning,
include responsive tables and keyboard focus styles, and send Cache-Control:
no-store. They never expose another learner's data through a session-ID parameter.

## Data preservation and release boundary

No schema migration is required. Analytics are derived; no stored performance
summaries, historical rewrites, scenario edits, or new research-group rules were
introduced. Milestone 4 release/tag v0.4.0 remains unchanged. Milestone 5 is packaged as release v0.5.0; the adaptive protocol version remains unchanged.

## Validation

The release validation rerun passed **69 tests, 0 failures, 0 skips**, in 295.34 seconds on
November 15, 2026, using the explicitly authorized disposable Supabase project.
All five production application-table hashes matched before and after the run.
The test project had zero remaining generated test schemas afterward.

Coverage includes calculations, empty denominators, zero response times, confidence
distributions, actual difficulty, response-weighted versus session-weighted
comparisons, incomplete-session exclusion, immediate/idempotent/atomic completion,
exact plans, read-only history, learner isolation, escaping, empty states, and
protected/idempotent next-session starts. All existing Milestone 4 regressions for
adaptation, control separation, ordering, pair exclusion, feedback, mistakes and
progress remain in the suite and passed.

Automatic approval review rejected a proposed validation command because its
TEST_DATABASE_URL fallback could direct schema-creating tests at production.
That command was not executed. The saved runner now requires an explicit,
separate disposable test target. `validation_support.py` identifies the project
from the documented Supabase direct hostname or shared-pooler username, rejects
the production project even if the URL uses another endpoint/port, and rejects
unverifiable routing overrides. It never falls back to DATABASE_URL. The database
fixture repeats this check before schema creation.

The user subsequently configured and authorized a distinct test project. Its URL
was verified distinct and an authenticated, certificate-verified, read-only
SELECT 1 succeeded before any schema-creating tests ran. No project identifiers,
passwords or URLs were printed. See [Supabase connection formats](https://supabase.com/docs/guides/database/connecting-to-postgres).

Configure TEST_DATABASE_URL locally for a separate disposable Supabase project
and authorize that target before running:

```bash
.venv/bin/python scripts/validate_milestone5.py
```

The test role must be able to create/drop generated schemas. Tests must not be
reported as integration-validated while those cases are excluded or skipped.
Production access was read-only for preservation snapshots. No production writes,
imports, migrations, server restarts or automatic backfills were performed.
No production configuration or credentials were changed.

## Remaining review points

The automated suite validates Flask-rendered screens and access control. The user
completed manual testing and recorded the Milestone 5 screencast. Existing unmarked historical sessions remain excluded from completed
comparisons rather than being silently repaired. Descriptive comparisons across
different scenario mixes are not controlled measures of learning. Elapsed time
includes interruptions. No new research protocol, statistical exclusion rule,
researcher dashboard or export is introduced by these learner-facing features.
