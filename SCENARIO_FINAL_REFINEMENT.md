# Milestone 6 — final targeted scenario refinement

Status: final local review candidate; no production activation or release.
The targeted refinement reviewed all 27 participant scenarios and changed six
proposals. The final copy cleanup additionally lowercases “when” after “For
SD-4926,” in `evercrest-adv-draft-legit-003`; the remaining 20 proposal objects
are identical to archived revision 3. See MILESTONE6_STATUS.md for current status.

## Browser review

- Previous running candidate: **http://127.0.0.1:5008/review** (snapshot before
  the final capitalization correction; the offline preview below is refreshed).
- Synthetic learner workflows: **http://127.0.0.1:5008/login**.
- Generated credentials: `/private/tmp/PHISHSENSE_FINAL_REVIEW_ACCOUNTS.txt`
  (0600, outside Git).
- Offline review: `/private/tmp/PHISHSENSE_FINAL_REVIEW.html`.
- Full per-item audit: `data/scenario_qc_final.json`.
- Previous content snapshot: `data/scenario_realism_revision3.json`.

Earlier review servers/schemas are preserved. The final candidate is a fresh
scenario-only copy in the verified disposable TEST_DATABASE_URL project, with new
synthetic accounts and no participant history copied. Reviewer answers and IDs
are deliberate on the separate review page; normal participant training does not
render them. Do not use the review launcher for participant data collection.

## Exactly what changed

| Scenario | Targeted edit | Reason / approval flag |
|---|---|---|
| `phish-0057` | Removed the no-rewards-enrollment statement from context; aligned feedback | Preserve the directory/destination evidence without pre-labelling the offer as unexpected. Email body is unchanged. |
| `phish-0059` | Changed the background to ordinary onboarding/payment-reference fields | Remove the narrative conclusion about missing release. The request/body and intended approval-substitution evidence are unchanged. |
| `legit-004` | Added an activity/device/profile reference comparison and an inert account-activity link | A participant checks AC-482, EG-LT-27, the mail profile and the service destination, rather than merely reading a password-change notice. Reapprove expanded evidence. |
| `legit-005` | Added receipt reference, amount, allocation, portal and reporting-close details | Legitimate financial work can have a link and deadline; compare multiple purchase-record details. Reapprove expanded evidence. |
| `legit-008` | Added a reporting job and available reschedule slot | Evaluate maintenance-window overlap, job timing and queue destination while retaining the IT notice format. Reapprove expanded evidence. |
| `legit-009` | Added a recorded statement/account/period comparison and harmless expected PDF card | Legitimate financial messages may include attachments. The expected delivery channel is new proposed evidence and needs approval. No actual PDF exists. |

The strongest foundation scenarios are preserved (with only the approved
SD-4926 capitalization correction): Bracken invoice
`phish-0052`, both Harbor consent cases, both supplier-audit cases, both
replacement-phone/MFA cases, and the independent diagnostic case. Tests compare
those proposal objects directly with the archived revision-3 snapshot, allowing
only that exact capitalization correction.
All IDs, classifications, difficulty labels, objectives, pair keys and original
provenance/base hashes are preserved. No adaptive or assignment code changed.

## Context, variety and remaining cues

Every scenario was checked for explicit rule/answer language in its context.
No direct prohibition or classification statement remains in the neutral records.
They still contain necessary facts such as an account ending, project task,
authorization state, approved destination, or learner action history. Removing
those facts would make some answers arbitrary; answer-relevant evidence is not
itself an impermissible answer key.

Both classes contain links and attachments, including ordinary financial/account
work and deadlines. The participant renderer does not consult classification or
difficulty to choose formatting. Native link inspection, Reply-To text,
permissions and attachment cards remain escaped and completely inert. There are
no email-driven external hrefs, downloads, OAuth actions, MFA prompts, credential
forms, scripts or remote resources. The application login is separate from the
simulated email, and uses synthetic credentials only in this sandbox.

No blanket claim of zero content-level cues is made. Residual review items:

- `phish-0003` and `phish-0009` remain easy/intermediate boundary candidates; their
  identity mismatches may be recognized with a single comparison.
- Executive payment requests remain concentrated in phishing items. This pass
  does not invent a new legitimate executive scenario or silently repurpose an ID.
- Two easy executable-attachment cases remain intentionally recognizable and
  somewhat redundant. That is a mechanism-coverage limitation, not a UI leak.
- Message lengths vary naturally; range overlap and matching UI do not prove
  equal empirical difficulty or remove every possible statistical cue.
- The four enhanced legitimate notifications now support multi-detail checking,
  but their retained intermediate ratings still need human/pilot validation.

Reviewer-only answers, source IDs, ratings and rationales are not projected by
participant templates. Opaque per-user/session references remain in links/forms;
numeric scenario plans are not newly issued in cookies. Original numeric IDs are
still stored server-side for response/evaluation logging. All 27 loaded database
rows are rendered in a dedicated leakage/security test, not just selected samples.

## Inventory and availability

| Difficulty | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy / beginner | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Advanced | 4 | 4 | 8 |
| **Total** | **13** | **14** | **27** |

All 27 remain available in the review copy. Intended classifications match the
original protected labels, and functional tests verify scoring/feedback against
those labels. Automated checks cannot prove empirical difficulty or universal
human agreement about an authored scenario's ground truth.

The intermediate pool supports the ten-item baseline plan. Control retains its
five intermediate baseline positions followed by easy, hard, intermediate, easy,
hard. Advanced selection still supports five pair-safe items and has no spare
capacity. Any relabeling or removal requires explicit approval and replacement-
capacity checks. No such changes were made.

## Validation record

Scenario-content checks passed, including exact six-item scope, preservation of
foundation objects and protected metadata, neutral-record heuristics, available
transaction evidence, inert destinations, mixed-class components and capacity.
Chrome hostile-content checks and the live final-review check passed: 27 cards,
new factual references, preserved Reply-To/permissions, no external hrefs or
visible training placeholders.

Bounded database/regression runs so far:

| Batch | Result | Duration |
|---|---|---:|
| Targeted content, all-27 rendering, opaque references, workflows/results | 29 passed | 107.30s |
| Adaptive/control, presentation and target guards | 57 passed | 142.78s |
| Database/matched-pair attempt | 13 passed; 1 connection-failed case; 1 teardown error | 53.23s |
| Controlled resumption of five incomplete matched-pair cases | 5 passed | 78.90s |
| Final security/isolation/mistakes batch | 33 passed | 40.58s |

The interruption was `OperationalError`, SQLSTATE None, category connection
refused, inside connection establishment before SQL, not an assertion failure.
Production hashes still matched for that failed batch. Its one generated schema
was checked against the failed synthetic fixture (one paired experimental user,
27 synthetic scenarios, one session, four responses, zero decisions), then removed
only after a fresh verified-TLS test connection succeeded. Review/manual schemas
were preserved. The five incomplete cases then passed in a new process; no full
batch was blindly retried and production was never a fallback.

Every completed batch reported matching production hashes and zero open observed
test connections. The resumed batch reported zero automated test schemas. The
final baseline/schema/ID checks are recorded after the last batch completes.
The final review schema is intentionally retained for the requested browser
review; earlier review/manual schemas are not automated-test leaks.

## Newly verified control-arm classification imbalance

A final read-only audit of the preserved control selector, using the actual
numeric IDs copied from production, produced classification sequence:

```text
Phishing, Phishing, Phishing, Phishing, Phishing,
Phishing, Phishing, Legitimate, Phishing, Phishing
```

This is **9 phishing / 1 legitimate**, with **5 phishing / 0 legitimate** in the
baseline block. The global 13/14 pool balance does not ensure balanced arm exposure.
The approved difficulty sequence is correct, but deterministic numeric-ID
preference overrepresents phishing cases. Experimental selection is different;
this is a material research-comparison confound and can create an answer-pattern
shortcut in the control arm.

No control selector, difficulty sequence, historical plan, group rule or adaptive
threshold was changed. A remedy requires explicit approval for a balanced,
predetermined control item list/new-session content protocol while preserving the
schedule and pair exclusions. A balanced control mix is feasible in the current
inventory, but it is not implemented or silently approved here. Existing saved
sessions must not be reinterpreted. Functional tests passing is not evidence that
this methodological issue is resolved.

## Remaining sign-off items

- Resolve the verified 9/1 control-item imbalance through an explicitly approved
  research-design/content-selection decision before participant collection.

- Approve the six evidence refinements, especially the statement PDF delivery,
  before participant use; current records remain draft-only.
- Treat ratings as provisional pending reviewer/pilot evidence. Do not relabel
  items or alter the approved adaptive thresholds to conceal a calibration issue.
- Agree on immutable content versions/snapshots before production activation.
  Updating text/techniques in place under existing IDs could change historical
  joins; no such update or migration is implemented here.
- The intermittent TCP-refusal root cause remains unproven. Successful bounded
  runs establish case coverage, not uninterrupted infrastructure reliability.

No production writes, history edits, imports, migrations, credential changes,
TLS weakening, group/protocol changes, commits, pushes, tags or application
version changes were performed. VERSION remains 0.5.0. This candidate can be
reviewed locally; it is not silently declared participant-ready or deployed.
