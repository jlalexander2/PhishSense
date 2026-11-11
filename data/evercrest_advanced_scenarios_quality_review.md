# Advanced draft quality review — revision 2, not approved

The original six drafts remain in `evercrest_advanced_scenarios_draft.json`.
Recommended replacements are in `evercrest_advanced_scenarios_draft_v2.json`.
The files use the same source IDs for revision tracking; they are alternatives,
not twelve distinct scenarios. No database connection or import was performed.

## Findings and revisions

1. **Difficulty:** The original legitimate emails were too instructional, and the
   first MFA draft explicitly said no replacement was requested. All six were
   revised. They are candidates for advanced training, not empirically validated
   advanced items. Reading length alone does not establish equal difficulty.
2. **Available evidence:** Each pair now has identical learner-visible reference
   context. Required facts are embedded in email_body because the current template
   does not separately render training_context. The learner compares permissions,
   fields/destination, or who initiated a sign-in. Feedback does not assume visible
   evidence establishes a compromised account or proves malicious attribution.
3. **Answer cues:** Removed statements such as “the notice matches” and “no new
   integration has been arranged,” and removed repeated anti-phishing instructions
   from legitimate messages. The reference record itself remains available so the
   task is answerable without guessing. Matched pairs use the same visible sender.
4. **Comparable complexity:** Each email has 111–120 whitespace-separated words,
   similar professional tone, and one primary comparison task. Phishing requests
   have plausible explanations; legitimate messages include external access,
   corporate data handling or authentication. Subject-matter complexity still
   differs and should be reviewed with representative learners before research use.
5. **Consistency/novelty:** Uses proposed fictional Evercrest partner workflows;
   these need researcher acceptance as company context. No source ID, subject or
   body duplicates the 19 approved records. Topics differ from existing generic
   invoice, urgent wire, maintenance, and reset emails. The internal matched pairs
   are deliberate contrasts, not duplicate emails.
6. **Concept accuracy:** Consent is different from password collection; excessive
   delegated permissions are the first attack's evidence. The audit pair tests
   authorization and release controls, not whether external recipients are always
   suspicious. The MFA attack is an unsolicited approval pretext, not necessarily
   repeated-prompt fatigue. Legitimate classification is conditional on the given
   independent scenario evidence, not on reassuring wording alone.
7. **Safety:** All sender and displayed destination domains end in .example.
   Email bodies contain no HTTP(S) URLs, executable HTML, active consent action,
   upload endpoint or attachment. Displayed previews are plain-text simulations.
   Required-field checks pass; the importer rejects all six as unapproved.

## Remaining review points

- Approve the proposed fictional directory/register/ticket context and vocabulary.
- Pilot comprehension and classification before treating advanced labels or
  matched-pair difficulty as validated.
- Closely related pairs may reveal cues when encountered together, especially
  with immediate feedback. Flag this for the study protocol; no sequence,
  allocation or adaptive threshold was changed during this content review.
- Learning objectives and review metadata are not stored by the current importer;
  retain this draft artifact. Learner context is retained inside email_body.

Concept references:
- Microsoft, consent phishing: https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/protect-against-consent-phishing
- Joint CISA/NSA/FBI/MS-ISAC phishing guidance: https://media.defense.gov/2023/Oct/18/2003322402/-1/-1/0/CSI-PHISHING-GUIDANCE.PDF
