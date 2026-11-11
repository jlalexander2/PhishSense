# Advanced scenario integration and pair exclusion

The project owner approved the six reviewed revision-2 scenarios and both
independent advanced scenarios. Their reviewed draft files remain unchanged.
`data/evercrest_advanced_approved.json` contains approved copies; the same eight
records are appended to `data/scenarios_approved_for_prototype.jsonl`. Original
JSONL bytes are retained. `data/advanced_approval_manifest.json` records source
checksums and IDs. The integration script compares reviewed fields before import.
Source IDs containing `draft` are retained as stable identifiers, not approval
status; the approved copies have `review_status: approved`.

## Persisted metadata

Migration `005_scenario_metadata.sql` adds nullable scenario fields:

- `training_context`: exact learner context, also retained in `email_body` for the existing template.
- `learning_objectives`: a JSONB array containing all reviewed objectives.
- `matched_pair_id`: a shared exclusion key, NULL for independent scenarios.
- `introduced_in_version`: content eligibility boundary for existing protocols.

The three keys are `evercrest-consent`, `evercrest-audit`, and
`evercrest-enrollment`, each shared by its phishing/legitimate pair. Both
independent scenarios have NULL pair keys. No existing scenario is assigned a
pair retroactively. The importer preserves these fields, validates metadata, and
skips existing source IDs without overwriting. The one-time integration script
also compares every imported content field and stops on a source-ID conflict.

## Selection and preservation

New sessions use `rules-v3-pair-exclusion`. Adaptive selection keeps the existing
unused-first, then oldest-completed preference while selecting at most one
member per pair. Reviewed scenarios also exclude their partners. Control
selection searches the predetermined difficulty schedule using a stable ID order,
without reading learner performance or completion history. Backtracking avoids
choosing a pair member that would make later scheduled positions impossible.
Both groups retain ten emails, sequential unlocks, the same response validation,
metrics and Evercrest interface. A server-side check rejects a conflicting new
session selection before recording a response.

The control schedule remains intermediate x5, easy, hard, intermediate, easy,
hard. Adaptive thresholds and group-assignment defaults are unchanged. Neither
existing session versions nor historical results are rewritten. Versions v1/v2
exclude the newly introduced content from future replacement selection, keeping
already-running sessions from changing behavior because the pool expanded.

## Capacity limitation

The advanced pool contains four phishing and four legitimate scenarios: three
matched pairs and two independent items. A five-hard block must choose one from
each pair and both independent items. There are eight valid five-item subsets,
with **no spare independent capacity**. Control requires only two compatible
hard items and keeps the approved fixed schedule. No additional class-balance
rule has been introduced.

The pool should be expanded and its difficulty piloted before participant
research. Removing either independent item makes five-hard promotion infeasible.
Repeated sessions will reuse scarce content under the existing reuse policy;
no new study exposure or session-count design is implied by this import.

## Applying safely

`python scripts/integrate_advanced.py` verifies source files without connecting.
After authorization, `python scripts/integrate_advanced.py --apply` applies the
additive schema and eight-record import in one transaction. It locks application
tables briefly, verifies existing fields unchanged, checks imported metadata and
both schedule capacities, and commits only if all checks pass. It does not create
participant sessions or change group assignments. Existing records are never
replaced to resolve conflicts. Restart Flask after successful integration.

## Current execution status

Migration 005 and all eight approved scenario inserts committed successfully in
one transaction. Every imported content field (including context, objectives and
pair IDs) was verified. The original fields of 1 account, 19 scenarios, 5 sessions,
6 responses and 0 evaluation records were compared before commit and remained
unchanged. No group assignments or historical session versions were changed.

| Difficulty | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Advanced | 4 | 4 | 8 |
| Total | 13 | 14 | 27 |

Live read-only checks verified the three two-member pairs, two independent
advanced scenarios, five compatible hard selections, and the approved fixed
control schedule with ten emails. All three SQLite files still match their
original checksums. Reviewed draft checksums and original approved JSONL bytes
were also verified. Flask has not been restarted.

The earlier endpoint refusal cleared without credential, endpoint or TLS changes.
DNS resolved three pooler addresses; TCP reachability and three consecutive
verified-TLS authenticated read-only connections succeeded. This is consistent
with a transient endpoint/network issue, but the exact earlier cause was not
established. No certificate verification was weakened.

Before the live import, the complete synthetic Supabase suite passed **43 tests**.
The post-import run was interrupted by renewed connectivity problems: **30
passed, 1 failed, 13 errors**. The failure/error count includes an affected test's
cleanup error. Database OperationalErrors appeared during setup/cleanup; the
post-import suite therefore did not pass. No code was changed between the
successful pre-import suite and this run. Temporary test-schema cleanup may be
incomplete because the connection was unavailable.

Further changes were stopped at the user's instruction. The authorized import
remains committed; there was no destructive rollback, reimport or Flask restart.
That interruption is now superseded by the successful validation below.

## Final post-import validation

The previously failed sequence test passed independently. The complete suite
subsequently passed **43 tests** against Supabase, with no connection failures.
All five public-table hashes remained unchanged. All 27 scenarios and imported
metadata, three matched pairs, two independent advanced items, hard-promotion
capacity and the fixed control schedule were verified. Both orphaned synthetic
test schemas were safely removed; zero test schemas remain. No import was
repeated and Flask was not restarted. See CONNECTIVITY_VALIDATION.md for measured
connection usage, investigation limits and the still-unconfirmed historical cause
of the intermittent endpoint refusals.
