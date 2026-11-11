# Milestone 4: recurring-mistake identification

No database migration is required. The summary is derived from existing
training_responses, training_sessions and scenario metadata. No response,
participant account, approved scenario, threshold or group assignment is rewritten.

## Approved rule and scope

At least two recorded incorrect classifications of the same error type by the
same learner are recurring. The cumulative summary covers that learner's recorded
training sessions, including historical training sessions. Pre-test and post-test
assessment records are excluded. Correct responses neither add to nor reset a
count. There is no rolling window or distinct-scenario requirement: separate
attempts on the same scenario across sessions are separate occurrences.

- Missed phishing: an incorrect response with user_answer=0.
- False alarm: an incorrect response with user_answer=1.

The stored correctness flag and submitted binary answer identify the error type,
so a future scenario-label edit does not reinterpret that primary historical
classification. Counts are recalculated on each read rather than duplicated in
a counter table. A single response ID is counted once.

## Metadata associations

For incorrect responses, exact nonempty phishing_technique labels and existing
learning_objectives are counted separately within each error type. Repeated
copies of the same objective on one scenario count once per response. Missing
metadata leaves the primary count intact and does not create an invented label.
No synonyms are merged, no written reasoning is inferred or scored, and no new
scenario categories or content are introduced.

An association is recurring when it occurs in at least two incorrect responses
of that error type. One response can have several objectives; association counts
must not be added as separate mistakes. Metadata associations describe exposure,
not proof that the learner misunderstood that exact concept. Associations reflect
current stored metadata; the underlying historical responses are unchanged.

## Read-only demonstration

From the learner dashboard choose **My Mistake Patterns**, or open `/mistakes`.
The page displays both primary counts, recurrence status, and available exact
metadata associations. It always uses the authenticated session's user ID, ignores
attempts to select another learner via query parameters, rejects POST, runs its
query in a read-only database transaction, and uses Cache-Control: no-store.
Labels are HTML escaped. No researcher dashboard, exports, roles or enrollment
features are included.

The existing per-response feedback page is unchanged. Neither experimental nor
control scenario selection reads the mistake summary, and existing adaptive
thresholds, ten-email length, ordering and pair exclusions remain unchanged.

## Demonstration sequence

Use a synthetic learner in the isolated manual sandbox; never deliberately insert
mistakes into a participant's actual research records. Restart only the sandbox
to load new code if it was already running.

1. Open My Mistake Patterns before training: both counts are zero.
2. Deliberately classify one phishing scenario as legitimate. Return to the summary:
   Missed phishing is 1 and Not recurring.
3. Make the same type of mistake on another phishing response: the count is 2 and
   Recurring. False alarms remains separate.
4. Classify a legitimate email as phishing to demonstrate the independent false-
   alarm count. Correct responses do not increase or reset either counter.
5. When incorrectly answered scenarios share an exact metadata label/objective,
   show its count in the associated metadata table. Missing labels are not invented.
6. Switch to another synthetic account and confirm its counts are independent.
7. Show normal feedback, progress and the unchanged experimental/control sequence.

The fixed control baseline includes both classifications. Metadata association
recurrence requires matching stored labels; different labels are intentionally
not merged merely to create a recurring example.

## Validation results

The complete Supabase suite passed **52 tests, 0 failures, 0 skips**. New tests
cover threshold boundaries, independent error types, correct-answer handling,
response-ID deduplication, exact metadata counting, repeated attempts across
sessions, assessment exclusion, both research groups, learner isolation,
authentication, HTML escaping and read-only page access. All existing adaptive,
control, feedback, progress, ordering and pair-exclusion tests still pass.

Chrome also verified the new dashboard link and summary page with isolated
synthetic learners: one showed two missed-phishing errors as recurring and one
false alarm as non-recurring, with existing metadata associations; the other
showed zero counts and no leaked associations. Both synthetic-table snapshots
and production-table hashes were unchanged by viewing the page. The generated
browser schema was removed. A screenshot is available locally at
`/private/tmp/phishsense-browser-checks/mistake-patterns.png`.

Production accounts, historical records, approved scenario content, adaptive
thresholds and group-assignment rules were not modified. No Milestone 5 features
or database migration were introduced. Restart only your isolated demo server
when ready to load the new page; no server was restarted during this change.
