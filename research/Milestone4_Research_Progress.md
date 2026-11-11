# PhishSense: Milestone 4 implementation progress

**Build:** v0.4.0 (Milestone 4)

Milestone 4 implements rule-based adaptive training alongside a fixed,
non-adaptive control workflow. The planned research comparison remains 15
experimental learners and 15 control learners. No participant outcomes or
statistical study findings are claimed by the software validation.

## Completed implementation

- SQLite was migrated to Supabase PostgreSQL, preserving original IDs, password
  hashes, scenarios, responses and session records. Local SQLite backups remain
  outside version control. TLS certificate and hostname verification is enforced.
- New sessions begin with five ordered intermediate scenarios. Experimental
  difficulty is evaluated after each five-response block using the approved
  accuracy, elapsed response-time and confidence rules.
- Control sessions follow intermediate x5, easy, hard, intermediate, easy, hard,
  independent of performance. Both groups retain ten ordered emails per session.
- The approved pool has 7 easy, 12 intermediate and 8 advanced scenarios. Three
  advanced matched pairs are mutually exclusive within a session; two advanced
  items are independent. Five-hard experimental blocks have no spare independent
  capacity, so expansion and pilot validation are recommended before research.
- Every response retains classification, correctness, reasoning, confidence,
  elapsed time, presented difficulty and timestamp. Five-response decisions retain
  metrics, protocol version, group and previous/proposed/applied difficulty.
- Immediate educational feedback explains each scenario. Recurring mistakes are
  identified per learner at two incorrect responses of the same error type:
  missed phishing or false alarms. Exact stored technique/objective associations
  are shown without inventing categories or scoring written reasoning.
- A read-only learner summary exposes only the authenticated learner's training
  patterns. Researcher dashboards, exports and administration remain Milestone 5.

## Validation and limits

The automated suite has 52 cases covering database integrity, authentication,
training/progress/feedback, threshold boundaries, fixed control behavior,
sequential validation, pair exclusion, historical protocol protection, recurrence
and learner isolation. Real Chrome testing also exercised both experimental
paths and contrasting control performance with synthetic accounts.

Integration tests use generated isolated schemas and synthetic data. Production
application-table hashes were compared before and after validation. No account
credentials or participant records are included in this submission.

Elapsed response time includes interruptions and is not an active-attention
measurement. The first training block includes immediate feedback and is not an
independent pre-test. Scenario difficulty has editorial approval but still needs
pilot evidence. Formal assessment workflows, participant enrollment and research
analysis/inclusion rules remain future work, subject to the approved protocol.

No adaptive thresholds, research-group allocation rules or participant records
were changed for the demonstration. See TESTING.md and the implementation notes
in the repository root for details.
