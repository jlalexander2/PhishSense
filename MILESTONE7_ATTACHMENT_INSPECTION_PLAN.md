# Planned Milestone 7 usability enhancement: attachment inspection

Status: deferred by the user; **not implemented or activated in Milestone 6**.
This is a scoped planning note, not authorization to begin Milestone 7 work.

Milestone 6 retains static attachment tiles. Filenames/extensions are plain text;
existing preview text is displayed beneath the filename when present. Clicking a
tile does not open a file. No real file is supplied.

## Proposed future behavior, subject to implementation approval

- Provide an accessible expandable inspection control using native details/summary
  or an equivalently accessible pattern. Support keyboard activation, visible
  focus, screen-reader naming/state, touch, readable text and adequate contrast.
  Inspection must not depend only on hover, color or pointer input.
- Reveal only approved plain-text preview evidence already associated with the
  scenario. Escape filenames and preview text; never render arbitrary HTML or
  interpret document contents. A consistent unavailable-preview state must not
  fabricate contents or imply that the attachment is safe or malicious.
- Keep filenames/extensions visible and use the same controls and styling across
  phishing/legitimate classes, difficulty levels and research groups. Do not
  project reviewer notes, classifications, hidden identifiers or future answers.
- Attachments remain completely inert: no real document opening, downloading,
  execution, network requests, remote resources, credential collection, embedded
  viewers, active content, external navigation or file-system access. No actual
  DOC/PDF/ZIP/executable is required for a text preview.
- Preserve all scenario IDs, provenance, answers, difficulty labels, pair rules,
  scoring, adaptive thresholds and historical responses. Adding new preview
  evidence requires separate content review; it is not a cosmetic change.

## Research and verification requirements before activation

Document the presentation version and its activation boundary. A change from
always-visible to expandable evidence may affect discoverability, response time
and empirical difficulty even if the words are unchanged. Do not change existing
research sessions or silently mix presentation versions during data collection.
Review any new preview text for cue leakage and comparable inspection opportunity.

Future validation should cover mouse/keyboard/touch and screen-reader behavior,
focus and expanded state, missing-preview handling, escaped hostile strings,
class-independent rendering, absence of remote requests/downloads/navigation and
unchanged scenario/response metadata. Use only approved disposable resources for
workflow tests. None of these implementation steps is started by this note.
