# Milestone 6 — Email realism refinement and review

## Changes available in code

`email_presentation.py` creates text, link-inspection and attachment components.
The training screen uses consistent typography and spacing for both classes.
Workplace context appears outside the email card. Where approved advanced bodies
contain the exact repeated context prefix, only that duplicate wrapper is removed
from the display; the context itself remains visible and stored content is intact.

Links look like ordinary underlined email links. Hover shows the apparent target;
selecting the label, or focusing it and pressing Enter, expands the full target.
Native `<details>/<summary>` controls provide this without JavaScript. There is
**no navigation href**, new window, external request, tracking or credential form.
Copying or opening the apparent target requires a deliberate action outside the
application; destinations are reserved fictional domains, not live services.

Only absolute HTTPS URLs with `.example` or `.test` hostnames are eligible for
inspection controls. Credentials, ports, IPs, look-through suffixes such as
`foo.example.real.com`, non-ASCII/invalid hostnames, backslashes, whitespace and
encoded controls are rejected. Other strings remain escaped text, not links.

New draft syntax is deliberately not HTML:

```text
[[link:View Payroll Statement|https://payroll.evercrest-group.example/employee/statement]]
[[attachment:REC-118_interview_packs.zip|Contents preview: Candidate-A.pdf, Candidate-B.pdf, Candidate-C.pdf]]
```

Existing full fictional HTTPS URLs are inspectable without rewriting the stored
URL. Legacy `[simulated attachment: filename — not downloadable]` wrappers become
consistent attachment cards. Filenames, extensions (especially `.exe`) and content
previews remain visible. No file, archive, executable command or attachment URL
exists behind a card. One uniform instruction outside the message explains the
interaction safety for every scenario, avoiding class-specific simulation labels.

All text and labels remain escaped; no email HTML is marked safe. Existing CSP
and script/resource restrictions remain active. The implementation consults no
classification, difficulty, group, source-ID pattern or correctness field when
building components. Styling is identical for equal content in both classes.

## Approved inventory stays unchanged

The approved JSONL and eight advanced source/approval files were not edited.
The approved pool remains 27 scenarios: 7 easy, 12 intermediate, 8 hard; 13 phishing
and 14 legitimate. Scenario IDs, labels, difficulties, objectives, explanations,
three matched-pair keys, adaptive rules and research groups remain unchanged.
No application path reads the proposed draft file. No imports or production
updates are performed. Existing obvious training URL text is **not silently
remapped**: replacing its destination requires review of the proposed content.

## Review-first corpus revisions

`data/scenario_realism_drafts.json` contains 27 proposed revisions, all explicitly
DRAFT, with an approved-source file hash and per-record hashes for comparison.
The standard importer rejects them because they are unapproved. The document is
not the approved dataset. Classification/difficulty and pair/objective metadata
are retained for review, not automatically re-approved or recalibrated.

The proposals use fictional Evercrest contacts, suppliers and providers, natural
workplace language and signatures. They cover HR, scheduling, IT, payroll-account
banking, procurement, travel, document sharing, audits and recruitment. Each
record includes review notes. None is automatically substituted into training.

| Scenarios | Why reviewer approval is required |
|---|---|
| All 19 legacy IDs (`phish-*`, `legit-*`) | Real brands/generic company domains become fictional identities. Added workplace context can change how confidently authenticity can be assessed. |
| `phish-0052`, `phish-0075` | The original PDF/DOC alone does not establish fraud. Proposed missing-invoice/dispute context adds evidence and may make these intermediate cases easier. |
| `phish-0059` | Proposed absence of a recorded approval strengthens the BEC evidence. Reassess intermediate difficulty. |
| `phish-0003` | The zero-for-letter lookalike is preserved but a new known domain is supplied; recognition difficulty may change. |
| `phish-0001`, `legit-009` | Payroll-account framing is new. Preserve the bank-verification concept and legitimate bookmarked-account access; explicitly approve the framing. |
| `legit-005` | A consumer streaming renewal becomes a business media subscription. Review purpose and source-metadata alignment. |
| All 8 advanced IDs | Context, permission scope and workflow evidence remain intact. The live renderer only relocates exact, unchanged context text; approve proposed normalized URL paths/link labels before content activation. |
| Consent pair | Both drafts deliberately show the same workspace target; excessive permissions remain the phishing indicator. A familiar host must not become a legitimacy shortcut. |
| Audit pair | `files.crestline-assurance.example` versus `audit.crestline-assurance.example` remains visible; do not collapse them into a shared safe-looking target. |
| Device-enrollment pair | No invented link is added. Who initiates the authenticator session remains decisive. |
| Independent diagnostic/recruitment cases | No command or real ZIP exists. Software Center bypass and expected encrypted PDF delivery remain their respective concepts. |

Original explanations and metadata are retained in the draft for comparison;
brand-specific references must be reviewed/aligned before approval. Polishing
emails is not proof of equivalent empirical difficulty. Pilot approved revisions
before participant research.

Some legitimate scenarios intentionally contain no link, while several phishing
scenarios contain links. That pre-existing corpus imbalance can itself become a
shortcut. Adding links to legitimate messages whose explanations explicitly rely
on no link would change their evidence. It is flagged for review, not corrected
silently. Tests demonstrate renderer parity, not the absence of every possible
content-level cue or bias.

## Local review preview

```bash
.venv/bin/python scripts/preview_scenario_realism.py
```

Open `/private/tmp/PHISHSENSE_EMAIL_REALISM_REVIEW.html` in a browser. It shows all
27 proposals with reviewer-only labels, notes and explanations, using the same
email components. This static file queries no database and is not a participant
route. It contains no account credentials, participant records or real addresses.
Its CSP blocks scripts and resources.

## History-preserving activation requires a later review

Do not approve/import this draft implicitly. Existing historical results join
scenario titles from the scenario table; overwriting titles/bodies under existing
IDs could change the evidence displayed for past sessions even if response rows
are untouched. Before activating revisions, agree on an immutable content-version
or snapshot policy for future sessions and explicitly review any required schema
work. No such migration, protocol change or in-place overwrite is implemented here.

## Validation

- 25 new offline presentation tests passed: fictional URL validation, unsafe
  destinations, escaped labels/files, inert inspection markup, preserved attachment
  evidence, exact context extraction, renderer parity and draft/base integrity.
- Chrome smoke check passed with hostile HTML, an inspectable fictional payroll
  link and attachment card; no injected executable elements or unsafe-resource
  requests. No database connection was used.
- Full 118-case run: 106 passed, one connection-failed test and one teardown
  connection error in 289.54 seconds. No skips were reported before stopping.
  Eleven tests were not reached; ten offline cases passed separately, and the
  other unreached workflow had passed its targeted run. There are 117 distinct
  successful cases across runs, not a full-suite pass.
- The newly blocked case is `test_empty_views_and_start_action_security`.
  Post-run production hash comparison and cleanup could not connect. Another
  generated schema may remain; its identity/count is unverified. No automatic
  retry or production fallback was attempted. Details are in MILESTONE6.md.

## Connectivity investigation (separate from corpus work)

The configured test endpoint is the session pooler on port 5432, in a verified
project distinct from production. DNS resolved three addresses. TLS certificate
verification and PostgreSQL authentication succeeded without changing credentials
or TLS settings. The observed database activity count was 8 against a database
`max_connections` of 60. This is not the pooler's client-connection limit; the
project dashboard is needed to establish that limit or incident history.

There is no conclusive evidence of DNS failure, an incorrect endpoint, or
connection exhaustion behind the previous interruption. Connections in the
reviewed fixtures/routes are closed; successful runs do not prove that an earlier
transient pooler/network interruption had a specific cause.

One generated `phishsense_test_*` schema remained. Its complete five-table
inventory, one `finish` synthetic user, one session, ten responses and two
adaptive evaluations matched the failed Milestone 5 test fixture. After verifying
the distinct test target and checking the fixture again, only that schema was
removed. Manual test schemas and all production schemas were preserved.

The previously blocked workflow then passed (1 test, 23.54 seconds), production
public-table hashes matched, and zero generated test schemas remained. An initial
local attempt was interrupted by a presentation-parser syntax edit; it did not
report a connection error, its teardown succeeded, and production hashes matched.
The syntax was fixed before the successful targeted run and full-suite run.

The subsequent full run suffered another connection interruption in a different
existing workflow (see validation above). Current point-in-time success does not
establish sustained connectivity. The pooler's incident/client-limit evidence
from the disposable project's dashboard is needed; no dashboard connector is
available in this session. Further database operations stopped. The old schema's
verified removal and targeted cleanup do not establish cleanup of this new run.

## Subsequent validation outcome — November 22, 2026

All 118 distinct tests now have passing results across bounded runs, including
the previously incomplete cases; no skips. There were 120 successful executions
because two integrity cases were repeated. One intermediate fixture setup still
encountered TCP connection refused (SQLSTATE None) before SQL; its empty generated
schema was identified and removed only after the independent six-minute read-only
check passed. Final generated-schema count: zero; manual-test schema retained.
Completed-batch and final saved-baseline production hashes matched. Failed runs'
unavailable hash checks remain documented, not retrospectively assumed.

The reported 23505, 23514 and 23503 entries correspond to expected negative-test
triggers, whose application/pytest exception handling passed. They are distinct
from the transport refusal. The probe sustained 36 held-connection and 36 fresh
authentication checks over 365.78 seconds, but the original intermittent refusal's
root cause remains unproven. See MILESTONE6.md for the complete batch record.
No draft approval, corpus activation, production update, commit, push or version
change was performed.

## Revision 2 — browser-review implementation

The project owner approved the overall direction and authorized disposable-project
implementation. All 27 proposals now include learner-visible context, revised
professional correspondence, and feedback aligned to the proposed evidence. The
six representative revisions informed the update. Each record remains explicitly
DRAFT with `participant_approval_required=true`; approval of direction is not
silently recorded as approval of every participant stimulus or its difficulty.

Priority evidence reviews:

- `phish-0052`: an otherwise plausible invoice asks for beneficiary 9168 instead
  of registered beneficiary 7042, postponing the required verification until after
  payment. The PDF itself is not the phishing evidence.
- `phish-0075`: an invoice-dispute worksheet directs the learner to enter an
  Evercrest password outside the independently recorded supplier portal/sign-in
  workflow. The DOC itself is not the phishing evidence. A separate fictional
  supplier/contact avoids inventing an additional matched pair with invoice 7832.
- `phish-0059`: a plausible executive payment request defers the required new-
  supplier approval until after payment. Retain intermediate provisionally and
  review whether the added evidence changes actual reasoning demands.

These cases retain their numeric/source IDs, classification and difficulty.
Legacy intent/technique/target-category metadata remain unchanged for traceability;
review their alignment with the expanded evidence, particularly the added
credential request in `phish-0075`, before participant use. No new mistake-category
mapping is silently activated in the approved research corpus.

Legitimate invoices, orders and project updates now include inspectable links;
the expected travel itinerary includes a PDF card. Deadlines and requests for
work appear in both classes. Some legitimate messages still intentionally use
existing bookmarks and no email link. Existing encrypted recruitment PDFs remain
legitimate within their independently supplied context. Hard permission, audit,
MFA and diagnostic concepts/objectives remain intact. No claim is made that word
count establishes difficulty or that all possible corpus-level shortcuts are gone.
For example, executive payment requests are still concentrated in phishing cases;
further balancing would require explicit content review rather than hidden edits.

### Isolated browser review

Open **http://127.0.0.1:5006/review** to inspect all 27 emails. Correct answers,
difficulty rationales and reapproval notes are reviewer-only, collapsed below each
message. The page is registered only by the local review launcher; the normal
application has no `/review` route. Learner training does not reveal those labels
before feedback. The workplace-context panel is visible before classification.

Optional synthetic workflows: **http://127.0.0.1:5006/login**. Credentials are in
`/private/tmp/PHISHSENSE_REALISM_REVIEW_ACCOUNTS.txt`, permission 0600, outside Git.
Both accounts start without seeded responses. Existing synthetic/manual accounts
and their records were not reset. The static local preview remains available at
`/private/tmp/PHISHSENSE_EMAIL_REALISM_REVIEW.html` without a database connection.

`scripts/serve_scenario_review.py` first verifies TEST_DATABASE_URL identifies a
project distinct from production, and authenticates it with verified TLS. It reads
only approved scenario rows from production in a read-only transaction, copying
no users, responses, sessions or evaluations. It creates a new
`phishsense_review_<uuid>` schema only in the disposable project. `scenario_review.py`
rejects public schemas, wrong projects, insecure connections and nonempty targets;
all writes are schema-qualified. It inserts only revised scenario presentations,
preserving original numeric IDs and protected metadata, then creates two fresh
synthetic accounts with generated credentials. No production import/update occurs.

The server binds only 127.0.0.1:5006, uses its own signing key/cookie and registers
review routes in that process alone. It is single-threaded to avoid environment-
patch races. Graceful Ctrl-C removes only its own review schema. That schema is
intentionally retained while the browser review is running; it is not a leaked
automated-test schema. Do not use this reviewer sandbox for participant research.

The review is a new dataset copy, not an overwrite/version change of existing
sessions. Production activation still needs an approved immutable content-version
or snapshot policy; existing joins to current scenario text are not rewritten.
No schema migration or historical backfill was introduced.

### Current validation

The new corpus/loader/real-workflow batch passed 22 cases in 80.21 seconds with
zero failures/skips. It includes both ten-email group workflows against all revised
scenarios; a strong experimental learner receives five hard scenarios and the
control follows its unchanged schedule despite incorrect answers. Metadata/pair
checks, read-only access and nonempty-target refusal also passed. Four additional
offline guard cases passed for missing/wrong project, public schema and missing
TLS. Production hashes matched and generated test schemas reached zero.

Chrome verified the live review: all 27 cards, visible context, the repaired
invoice evidence, no placeholder bodies and no external hrefs. The independent
hostile-content/inert-link smoke check also passed with zero unsafe-resource
requests. Final bounded regression results are recorded below.

### Final revision-2 result

All 127 distinct current tests have passing results, with no skips, across bounded
batches of 22, 50, 18 and 42 cases, followed by a nine-case rerun against the final
refinements. Overlapping cases were deliberately rechecked; do not sum these as
distinct tests. The final runs reported matching production hashes, zero open
test connections and zero automated test schemas. Chrome security and live-page
checks passed. The review schema alone remains intentionally available for your
browser review; existing manual accounts remain untouched.

An easy-level length check found that the phishing drafts were consistently
shorter than the legitimate ones. Four phishing drafts gained ordinary business
references/closing detail without removing their recognizable warning signs.
The corpus check now requires overlapping body-length ranges within each level:
easy 69–85 phishing versus 80–84 legitimate, intermediate 39–103 versus 35–88,
and hard 105–118 versus 107–120 words. This prevents a perfect simple length
separation in these groups; it is not a difficulty metric or proof of no bias.
Ratings remain based on the evidence comparisons and require participant-use
review/piloting, not word count.

The final read-only numeric-ID comparison between production and the review copy
matched for every source ID, classification, difficulty and matched-pair key.
All older production records matched an earlier saved baseline exactly; its
additional completed-session activity predates revision preparation. All run-
scoped production hash checks matched. See MILESTONE6.md for the full evidence.
No commit, push, tag, version change or production content activation occurred.

## Third review revision

The current local draft is revision 3. Revision 2 is preserved in
`data/scenario_realism_revision2.json` and its separate browser schema. The latest
reviewer-only audit is SCENARIO_QC_REVISION3.md; per-item metadata is in
`data/scenario_qc_revision3.json`. View revision 3 at
http://127.0.0.1:5007/review. All 133 current tests have passing bounded-run
evidence, with no skips and zero automated test schemas. Ratings remain
provisional; explicit mechanism/pair/content-version approvals are still needed
before participant use. No approved scenario or production record was updated.

## Final targeted refinement

Six proposals were refined; the other 21 and all foundation cases are preserved
exactly. The candidate remains revision 3 with a final-targeted pass marker and
a new isolated review copy on port 5008. Source revision 3 is archived separately.
SCENARIO_FINAL_REFINEMENT.md and data/scenario_qc_final.json contain the full
per-item audit, 137-case validation, cleanup/provenance checks, and unresolved
calibration/operational issues. The read-only audit additionally verified a 9/1
control classification mix; balancing it requires explicit approval and was not
part of this content refinement. No production update or release occurred.
