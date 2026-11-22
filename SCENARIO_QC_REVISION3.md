# PhishSense scenario quality audit — review revision 3

Status: local review implementation; no participant activation or release.
All 27 unique scenarios were reviewed. The approved JSONL, original source drafts,
approval manifest and existing production data remain unchanged. Revision 2 is
archived separately in `data/scenario_realism_revision2.json`; its used browser
copy on port 5006 was not reset.

## Review in the browser

- Revision 3: **http://127.0.0.1:5007/review**.
- Synthetic learner workflows: **http://127.0.0.1:5007/login**.
- Local generated credentials: `/private/tmp/PHISHSENSE_REVISION3_REVIEW_ACCOUNTS.txt`
  (permission 0600, outside Git). Credentials are never embedded in source/docs.
- Offline reviewer preview: `/private/tmp/PHISHSENSE_REVISION3_REVIEW.html`.
- Complete reviewer-only item metadata: `data/scenario_qc_revision3.json`.

Reviewer pages deliberately show IDs, labels and notes. They exist only in the
loopback review launcher, not the normal Flask app. Participant training displays
none of that reviewer material. The revision-3 schema is a new empty copy in the
explicitly separate TEST_DATABASE_URL project; no participant accounts, sessions,
responses or evaluations were copied. Two newly generated synthetic accounts
allow full workflow review. Original numeric IDs are preserved in that copy.

## Changes across the entire corpus

- Explicit prohibitions were replaced with business records: supplier references,
  invoice/account details, purchase entries, project assignments, IT change/event
  records and recruitment delivery facts. Context no longer quotes the exact
  security rule the message violates. Relevant facts remain visible before the
  answer; difficulty is not created by withholding them.
- Formats include automated notices, short internal discussions, a business
  digest, supplier correspondence, a quoted invoice thread and external project
  invitations. The most common exact opening occurs once, rather than “Hello,”
  appearing in 22 of 27 messages. Different lengths reflect different genres;
  they are not used as the difficulty definition.
- Legitimate cases include deadlines, invoice/cost-allocation discussions, links,
  account events, split shipments and attachments. Repetitive sender reassurance
  and safety coaching were reduced. A deadline, external supplier, PDF or ZIP is
  not coded as a class-specific visual warning.
- Reply-To is shown as escaped fictional text where authored, including legitimate
  messages. No mailto or reply action is attached.
- Both consent-pair members use the same inert link-inspection component to show
  destination, application name and requested permissions. The scopes differ
  meaningfully; the controls/styles do not reveal the classification.
- Destinations are reserved fictional HTTPS URLs. Inspection performs no request,
  consent, sign-in, script, frame, download or external navigation. Attachment
  previews are harmless text. All fields remain escaped and CSP stays active.

A neutral record can still contain answer-relevant facts: e.g. a recorded
beneficiary or a last portal action. Removing those facts would make some answers
arbitrary. The difference is that the record supplies evidence, not an instruction
such as “never do exactly what the next email asks.” Authored phishing labels do
not prove how a real mailbox was compromised; feedback directs independent
verification rather than making unsupported forensic claims.

## Explicit approval items before participant use

All revised stimuli remain DRAFT. The user's request authorizes local revision-3
implementation, not silent production activation or empirical calibration.

| Item(s) | Change requiring approval |
|---|---|
| `phish-0052` | Invoice-thread impersonation, new Reply-To evidence and beneficiary diversion; replaces the old attachment-centered mechanism metadata. |
| `phish-0075` | Work-credential request at an unrecorded destination; corrected credential-harvesting intent/technique. |
| `phish-0001`, `phish-0009` | Mechanism terminology aligned with the revised evidence: bank-service credential pretext and executive identity impersonation, rather than unsupported urgency/compromise assumptions. |
| `phish-0059` | Neutral transaction status replaces the explicit finance rule; approval-substitution evidence must remain defensible. |
| All three advanced pairs | Context/presentation reviewed jointly; consent permission evidence moves into an equivalent passive inspection panel. Original exclusion keys stay unchanged. |
| All other revisions | New wording/background facts and difficulty equivalence; no new record is automatically marked approved. |
| Any future relabeling | Pilot/reviewer decision plus replacement capacity verification and study-content version approval. |

Original source IDs, base hashes, dataset provenance and original technique names
are retained in reviewer-only metadata. Corrected mechanisms apply only to the
new review copy; historical concept associations are not rewritten. The full JSON
audit records each item's intended clues, benign counter-cues, rationale,
provenance, pair key, approval needs and `empirical_difficulty_validated=false`.

## Difficulty and pool capacity

| Existing level | Phishing | Legitimate | Total |
|---|---:|---:|---:|
| Easy / beginner | 4 | 3 | 7 |
| Intermediate | 5 | 7 | 12 |
| Hard / advanced | 4 | 4 | 8 |

No label was changed. A new experimental inbox still needs ten intermediate
items; twelve exist. The fixed control schedule still has six intermediate, two
easy and two hard positions. The advanced pool supports exactly five pair-safe
items: one from each of three pairs plus both independent scenarios, with no spare
capacity. Pure selection tests verify these capacities and reject a request for
six pair-safe hard items. No replacement or new scenario is automatically approved.

Lower-demand intermediate candidates remain flagged: `legit-004`, `legit-005`,
`legit-008`, `legit-009`, with `phish-0003` and `phish-0009` at the easy/intermediate
boundary. Legitimate billing, fulfillment and project-action cases now involve
more than a simple notice; this does not justify pretending every retained label
has been empirically validated. Relabeling several candidates without reviewed
replacements would break the intermediate pool. Hard pair ratings also require
joint pilot review. The adaptive thresholds remain unchanged; new reading loads
must be considered when piloting response-time-based evaluations.

## Opaque participant references and history

Participant inbox links and answer forms now carry per-user/session HMAC-SHA256
references bound to a random session nonce. Numeric scenario IDs and plans are
not newly serialized into browser cookies. The authoritative plan remains the
existing PostgreSQL JSONB plan. Numeric GET/POST references are rejected; guessed,
wrong-user, wrong-session, stale and replayed references cannot bypass ownership,
ordering or completed-response checks. Original numeric IDs are still logged with
responses, confidence, reasoning, time and difficulty. No adaptive/control code,
group-assignment rule or research record format was changed.

The old tests now explicitly mint opaque references from fixture IDs and read
plans from the disposable database; they do not disable participant guards. New
tests submit raw IDs directly and replay the entire old signed cookie to check
that neither can append an unintended response. Reviewer IDs remain visible only
in the deliberately separate review UI.

Legacy unfinished rows without a saved plan cannot safely reconstruct that plan
from a cookie under the new interface. They receive an explanatory 409 page with
a protected Start a new session action; the historical row is left unchanged.
Tests verify this explicit transition and exact row preservation. Old numeric
bookmarks/forms require reloading the inbox after a future deployment. No live
server was upgraded or historical plan backfilled. Review this compatibility
behavior before deploying the local app change.

The optional `presentation_metadata` JSONB column is added only inside the empty
review/test copy after project/schema guards. The canonical schema and production
schema were not changed; normal rendering tolerates its absence. Future
production content activation requires a separately approved immutable version/
snapshot plan, including text and mechanism metadata. An in-place update under
existing IDs would change historical joins and is not implemented.

## Validation

All **133 distinct current cases passed**, no skips, across bounded batches:

| Batch | Passed | Duration |
|---|---:|---:|
| Opaque references, revised corpus and performance | 24 | 100.70s |
| Adaptive/control, rendering and target guards | 57 | 142.53s |
| Database and matched-pair regression | 18 | 123.78s |
| Security, isolation, mistakes and legacy-plan preservation | 34 | 49.72s |

The strengthened legacy form assertion was rechecked independently (1 passed in
5.72s) after the final fallback form was added. All completed batches reported
matching production hashes, zero open test connections and zero generated
`phishsense_test_*` schemas. These are bounded runs, not a claim of an uninterrupted
single-process run. Earlier connection refusals remain an operational history;
no connection error occurred in these revision-3 batches.

Coverage includes both ten-response workflows, promotion to five distinct hard
items, performance-independent control order, pair exclusions, required input,
feedback, response data, results, history, recurring mistakes, escaping, opaque
reference binding, raw-ID refusal, Cookie plan removal, full-cookie replay,
metadata projection, safe permissions, capacity and legacy compatibility.

Chrome hostile-content safety passed with no injected executable elements or
unsafe-resource requests. Live Chrome verification showed all 27 cards, Reply-To,
paired permission previews and no external hrefs/placeholders. The review's
frozen content hash and source-to-copy IDs/labels/pairs are checked separately.
One revision-3 schema remains intentionally available on port 5007. Revision 2
and the existing manual-test schema remain intact; they are not leaked automated
test schemas.

No production writes, imports, migrations, credential/TLS changes, research-rule
changes, commits, pushes, tags or application version changes were performed.
Application VERSION remains 0.5.0. Final participant-use approval, empirical
calibration and content freezing remain outstanding review decisions.
