# PhishSense

**Version:** v0.4.0 (Milestone 4)

**Status:** Milestone 4 complete; development prototype

**Project Type:** Master's Capstone — Cybersecurity Awareness Training

## Project Overview

PhishSense is a browser-based phishing-awareness training application designed to help users recognize phishing emails through simulated workplace scenarios, interactive email classification, immediate educational feedback, and rule-based adaptive learning.

The application uses Python, Flask, PostgreSQL (Supabase), HTML, and CSS. Milestones 1–3 used SQLite.

PhishSense aims to provide a more engaging alternative to traditional phishing-awareness quizzes by allowing learners to review simulated emails in a realistic corporate inbox.

The long-term objective is to evaluate whether adaptive phishing-awareness training can improve users' ability to recognize phishing attempts compared with non-adaptive training.

## Current Development Version

**PhishSense v0.4.0 (Milestone 4)**

This version adds approved rule-based adaptation, fixed control scheduling, recurring-mistake summaries, and Supabase PostgreSQL storage.

Implemented features include:

- User registration and login
- Secure password hashing
- Session-based authentication
- Personalized learner dashboard
- Simulated corporate email inbox
- Ten-email training sessions
- Phishing and legitimate email classification
- Written explanations for classification decisions
- Confidence ratings from 1 to 5
- Immediate educational feedback
- Training progress tracking
- Prevention of duplicate responses within a training session
- Supabase PostgreSQL storage of scenarios, sessions, and responses
- Five-response adaptive evaluations using accuracy, response time, and confidence
- Performance-independent control schedule and sequential completion
- Matched-pair exclusion for advanced scenarios
- Learner-specific recurring-mistake tracking and read-only summary

Researcher dashboards, exports, and additional research administration are deferred to Milestone 5. Gamification and formal assessments remain future work.

## Evercrest Group: Simulated Training Environment

PhishSense uses a fictional organization named **Evercrest Group** to provide a consistent workplace setting for its training scenarios.

Instead of answering isolated quiz questions, learners interact with a simulated employee inbox containing phishing and legitimate messages.

The inbox displays email senders, subject lines, and review statuses. Learners complete messages in the required order, classify each email, and receive immediate feedback.

The interface also displays a progress bar showing how many emails have been reviewed during the current training session.

Evercrest Group will eventually support the application's gamification features.

Planned gamification concepts include:

- A simulated company security budget
- Points awarded for appropriate security decisions
- Progression through security-awareness achievements
- Performance-based recognition
- A company-protection theme that connects training decisions to simulated organizational outcomes

These features are not yet implemented.

## Technologies

- **Python:** Application logic and database operations
- **Flask:** Web application framework
- **PostgreSQL / Supabase:** Relational database (Milestone 4 migration)
- **SQL:** Database schema and queries
- **HTML:** Application interfaces
- **CSS:** Interface styling
- **Werkzeug:** Password hashing and verification
- **Visual Studio Code:** Development environment
- **Git and GitHub:** Version control

## Database Architecture

PhishSense uses five application tables: users, training_scenarios, training_sessions, training_responses, and difficulty_evaluations.

### Users

Stores account information, including usernames, email addresses, password hashes, and account creation dates.

### Training Scenarios

Stores simulated phishing and legitimate emails.

Scenario information includes:

- Sender name and email address
- Email subject and body
- Correct classification
- Difficulty level
- Educational explanation
- Phishing intent and technique, where applicable
- Scenario source information

### Training Sessions

Tracks individual training sessions associated with registered users.

The database structure supports pre-tests, training sessions, and post-tests.

### Training Responses

Records individual learner responses, including:

- Training session identifier
- Scenario identifier
- Selected classification
- Classification accuracy
- Written reasoning
- Confidence rating
- Response time
- Scenario difficulty at the time of the response

### Difficulty Evaluations

Stores each five-response block's accuracy, median response time, mean confidence,
previous/proposed/applied difficulty, decision reason, group snapshot, and protocol
version. Protocol versions describe training behavior; they are independent of the
application release version.

### Database Relationships

- One user can have multiple training sessions.
- One training session can contain multiple responses.
- Each training response references a training scenario.
- Each difficulty evaluation references its training session.

Foreign-key relationships are used to maintain referential integrity.

## Milestone 4: baseline and adaptive training

T14/T15 now use the approved five-response rules and intermediate baseline.
See [ADAPTIVE_TRAINING.md](ADAPTIVE_TRAINING.md) for thresholds, selection,
group handling, research audit records, availability limits, and schema setup.
New sessions enforce response order for both groups. Controls use the approved
fixed mixed schedule, gated on six intermediate, two easy and two pair-compatible
hard scenarios. The approved pool now contains 7 easy, 12 intermediate and
8 advanced scenarios. Pair exclusion applies to both research groups.
Existing session versions and historical results are preserved.
Existing and newly registered accounts remain **unassigned and non-adaptive**
until explicitly assigned under the study protocol. Experimental learners can
receive five pair-compatible hard scenarios after qualifying baseline performance.
The hard pool has no spare independent capacity; expand and pilot it before
participant research. See [SCENARIO_INTEGRATION.md](SCENARIO_INTEGRATION.md).

Milestone 4 also includes a read-only learner mistake summary at `/mistakes`.
Two incorrect responses of the same type are recurring; missed phishing and
false alarms are tracked separately across training sessions. Exact existing
technique/objective associations are shown where available. See
[MISTAKE_TRACKING.md](MISTAKE_TRACKING.md). No migration or adaptive-rule change
is required. Researcher administration and exports remain deferred to Milestone 5.

## Application Workflow

The current training workflow follows these steps:

1. A learner creates an account or logs in.
2. The learner accesses the PhishSense dashboard.
3. The learner opens the Evercrest Group employee inbox.
4. The application presents ten training scenarios.
5. The learner opens the next available email; later emails remain locked.
6. The learner reviews the sender, subject, and message content.
7. The learner classifies the message as phishing or legitimate.
8. The learner provides a written explanation.
9. The learner selects a confidence rating.
10. The application records the response in PostgreSQL.
11. The learner receives immediate educational feedback.
12. The learner returns to the inbox, where progress and review status are updated.

The current prototype supports the core workflow. Additional functionality will be introduced in later milestones.

## Development Progress

### Milestone 1: Database Foundation

Completed:

- Created the initial SQLite database schema.
- Implemented the users, training_scenarios, training_sessions, and training_responses tables.
- Established primary-key and foreign-key relationships.
- Verified database integrity.
- Tested foreign-key enforcement.
- Confirmed that temporary test records could be rolled back.

### Milestone 2: User Authentication and Dashboard

Completed:

- Created the Flask web application.
- Implemented user registration.
- Connected registration to the SQLite database.
- Implemented password hashing.
- Added login and logout functionality.
- Implemented session-based authentication.
- Created a personalized learner dashboard.
- Added initial navigation and placeholder pages.
- Verified authentication and protected-route behavior.

### Milestone 3: Interactive Training Prototype

Completed:

- Reviewed and adapted phishing and legitimate email scenarios.
- Created a scenario import script.
- Populated the training database with approved prototype scenarios.
- Introduced the fictional Evercrest Group environment.
- Developed a simulated employee inbox.
- Implemented ten-email training sessions.
- Added email selection and review-status tracking.
- Implemented phishing and legitimate classification.
- Added required written reasoning.
- Added confidence ratings.
- Implemented immediate educational feedback.
- Added training progress tracking.
- Extended database response recording.
- Tested the classification and feedback workflow.
- Verified that the inbox updates after a completed response.

The Milestone 3 prototype establishes the foundation for adaptive training and future gamification.

### Milestone 4: Adaptive Training and Recurring Mistakes

Completed:

- Migrated SQLite storage to Supabase PostgreSQL with verified TLS.
- Added five-response experimental difficulty evaluation and fixed control scheduling.
- Preserved ten-email sequential training and existing response feedback/progress.
- Expanded the approved scenario pool to 27 emails and enforced advanced matched-pair exclusions.
- Added learner-specific recurring-mistake counts and a read-only summary.
- Validated the completed application with 52 passing Supabase tests and synthetic browser workflows.

The release is **v0.4.0 (Milestone 4)**. Researcher dashboards, data exports, and
additional research administration remain deferred to Milestone 5.

## Research Overview

PhishSense is being developed as both a software application and a research project.

The proposed study will investigate whether adaptive phishing-awareness training improves phishing identification performance compared with non-adaptive training.

### Proposed Research Design

The current study design proposes approximately 30 participants divided into two groups:

- **Control Group:** Approximately 15 participants receiving non-adaptive phishing-awareness training.
- **Experimental Group:** Approximately 15 participants receiving adaptive phishing-awareness training.

Both groups are intended to use a comparable training interface.

The primary difference will be whether the training difficulty and scenario selection adapt to learner performance.

### Planned Performance Measures

The application is being designed to collect:

- Classification accuracy
- Response time
- Confidence ratings
- Written explanations for classification decisions
- Scenario difficulty
- Training session progress

These measures may support comparisons between the control and experimental groups.

### Current Research Status

The proposed study design has been outlined, and the application now includes initial mechanisms for collecting training responses.

The adaptive and fixed control workflows are implemented and validated. Formal participant evaluation and research administration remain future work.

No formal participant-study findings are reported at this stage.

Participant recruitment and research data collection will be conducted only after the required approvals are obtained.

## Training Scenario Dataset and Attribution

The initial PhishSense training scenarios were developed using a publicly available phishing and benign email dataset as source material.

**Dataset:** Phishing and Benign Email Dataset  
**Repository:** Teddyha/phishing_benign_email_dataset  
**Platform:** Hugging Face  
**Source:** https://huggingface.co/datasets/Teddyha/phishing_benign_email_dataset

The Teddyha dataset repository identifies itself as a duplicate of:

https://huggingface.co/datasets/darkknight25/phishing_benign_email_dataset

The dataset contains examples of phishing and legitimate emails with classification labels and associated information about phishing techniques, intent, and targets.

For PhishSense, selected examples were reviewed and adapted into training scenarios compatible with the application's database structure.

Adaptations include preparing sender information, educational explanations, difficulty classifications, and simulated representations of potentially unsafe content.

The original dataset and the adapted PhishSense scenarios should not be treated as independently authored source material.

The dataset is identified as being distributed under the MIT License. Any redistribution of adapted dataset content must retain the applicable copyright and license notices.

The current prototype scenarios are intended for educational simulation, not real-world phishing activity.

## Project Structure

The repository includes the following components:

| File or Directory | Purpose |
|---|---|
| `VERSION` | Application release version (independent of training protocol versions) |
| `app.py` | Main Flask application |
| `adaptive.py` | Approved adaptive/control selection and difficulty rules |
| `mistakes.py` | Read-only recurring-mistake summaries |
| `database.py` | Verified-TLS PostgreSQL connections |
| `schema.sql` | PostgreSQL database schema |
| `import_scenarios.py` | Imports approved training scenarios |
| `templates/` | HTML application templates |
| `templates/dashboard.html` | Learner dashboard |
| `templates/inbox.html` | Simulated corporate inbox |
| `templates/training.html` | Email review and classification |
| `templates/training_feedback.html` | Educational feedback |
| `templates/login.html` | Login interface |
| `templates/register.html` | Registration interface |
| `data/scenarios_approved_for_prototype.jsonl` | Approved prototype training scenarios |
| `README.md` | Project documentation |

SQLite database files, local database backups, and the Python virtual environment are excluded from version control.

## Supabase PostgreSQL setup

The runtime now uses PostgreSQL through psycopg. Supabase authentication is not
used: Flask sessions and existing Werkzeug password hashes are retained. The
Evercrest training interface is preserved. The existing SQLite data has been migrated and the adaptive/control workflows tested
against Supabase. See `MIGRATION_REPORT.md` for validation details.

1. Create a separate Supabase development project. Obtain the direct or **session
   pooler** PostgreSQL URI from Connect (session mode supports IPv4). Download the
   project CA certificate if needed (see TLS trust below). See [Supabase connections](https://supabase.com/docs/guides/database/connecting-to-postgres).
2. Create/activate a virtual environment, then install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   cp .env.example .env
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```

3. Edit ignored `.env` locally: set `DATABASE_URL`, `PGSSLROOTCERT` (absolute CA
   certificate path), and `PHISHSENSE_SECRET_KEY` (generated value). URL-encode
   special characters in the database password. Never paste credentials into
   issues/chat or commit them. `.env` loads automatically; exported variables
   take precedence. TLS always uses `verify-full`, even if the URI requests less.
   Use a database role that can access the tables; the schema owner works for
   initial development. RLS is enabled with no Data API policies, so browser
   anonymous/authenticated roles cannot read learner data. A restricted backend
   role needs explicit grants and an appropriate RLS policy before use.
4. Review `schema.sql` and confirm the target has none of the five application
   tables. After approving that target, initialize it once:

   ```bash
   python -c 'from database import get_db_connection; from pathlib import Path; c=get_db_connection(); c.execute(Path("schema.sql").read_text()); c.commit(); c.close()'
   ```

   This is transactional and intentionally fails on existing tables rather than
   silently treating an incompatible schema as current. Do not drop existing
   tables. No schema initialization occurs automatically at application startup.
5. Preview the existing SQLite database (read-only, counts only):

   ```bash
   python migrate_sqlite.py phishsense.db
   ```

   Review counts and approve uploading these accounts/responses to your chosen
   Supabase project before running:

   ```bash
   python migrate_sqlite.py phishsense.db --apply
   ```

   Type `MIGRATE` when prompted. All four target tables must be empty. Copying is
   atomic, retains IDs, hashes, scenario fields and responses, verifies field
   values, and resets identity counters transactionally. SQLite timestamps without
   a timezone are interpreted as UTC (SQLite CURRENT_TIMESTAMP convention).
   The source and backups are never written. The tool locks target tables during
   copying; run it before starting the app. A failure rolls back the copy. Do not
   import scenarios first if you intend to migrate existing records.
6. For a fresh installation without legacy records, preview approved scenarios
   with `python import_scenarios.py`, then run `python import_scenarios.py --import`
   and type `IMPORT`. Importing skips existing source IDs, validates approval,
   and commits atomically. Review the dataset before uploading it.
7. Start with `python app.py`. Visit http://127.0.0.1:5000. Keep the Flask secret
   stable to preserve signed sessions; a changed secret requires logging in again.
   Debug mode is off by default. This remains a development application.

### TLS trust and read-only connection check

`database.py` always enforces `sslmode=verify-full`, checking the certificate
chain and hostname. `PGSSLROOTCERT=system` (or unset/blank) uses libpq's
OpenSSL trust store on libpq 16+. This is not necessarily the macOS Keychain.
An absolute path to a trusted PEM CA bundle is also supported. Missing explicit
CA files fail with a configuration error; verification is never weakened.

The configured session pooler failed verification with both the driver's system
store and `/etc/ssl/cert.pem` during development. Supabase's public CA was fetched
with verified HTTPS from
`https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt`
and saved locally as ignored `certs/supabase-ca.crt`. The local `.env` points to
that file. Using it now passes database authentication and verified TLS connection checks.
The migration and Supabase workflow validation are recorded in `MIGRATION_REPORT.md`.
Supabase documents its CA requirement in [SSL enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement).

Run `python scripts/check_connection.py` for a credential-safe diagnostic. It
opens a read-only transaction and runs only `SELECT 1`; it does not initialize
tables, migrate data, or print connection strings or raw driver errors.

### Automated migration validation

```bash
python -m pytest -q
```

Without `TEST_DATABASE_URL`, configuration checks run and PostgreSQL integration
tests explicitly skip. For Supabase validation, put a **separate development
project's** direct/session-pooler URI in `TEST_DATABASE_URL` in `.env`; configure
its certificate through `PGSSLROOTCERT`. The role must create/drop schemas.
Tests create a unique `phishsense_test_*` schema, use synthetic accounts and
scenarios, then drop only that generated schema. They exercise registration,
duplicate registration, password verification, authentication, import idempotency,
ten-email completion, classification, reasoning, confidence, feedback, progress,
invalid/replayed submissions, constraints, rollback, and SQLite migration.
No public application tables or real user records are used by these tests.
Do not treat skipped tests as evidence of a successful migration.

After automated tests pass against Supabase, migrate the approved source and
manually verify login with an existing account, Evercrest inbox submission,
feedback and progress. Record results without capturing credentials or personal
data. Keep SQLite backups for rollback; to run the old SQLite application, use a
separate checkout of the Milestone 3 version. New PostgreSQL responses are not
synchronized back to SQLite.

## Testing and Validation

### Database Testing

- Created and verified the initial database tables.
- Tested foreign-key enforcement.
- Verified database integrity.
- Confirmed that test records could be rolled back.

### Authentication Testing

- Tested user registration.
- Tested login and logout.
- Verified password hashing.
- Verified protected-page redirects.
- Confirmed personalized dashboard access.

### Training Workflow Testing

- Confirmed that the simulated inbox loads.
- Verified that ten scenarios are displayed.
- Opened a training email.
- Submitted a classification, written explanation, and confidence rating.
- Confirmed that educational feedback displays.
- Returned to the inbox.
- Verified that progress increased after the response.
- Confirmed that the reviewed email was marked as completed.

Initial SQLite response recording has also been verified.

The complete Supabase suite contains 52 tests. See [TESTING.md](TESTING.md) for coverage, isolation, and validation instructions.

## Planned Development

Future milestones will focus on:

1. Improving the realism and complexity of simulated email scenarios.
2. Introducing safe, realistic-looking links and attachment representations.
3. Expanding and piloting the approved scenario pool.
4. Preparing approved participant enrollment and research administration.
5. Adding pre-training and post-training assessments.
6. Developing the learner results dashboard.
7. Implementing training history and performance visualization.
8. Adding Evercrest Group gamification features.
9. Expanding application testing.
10. Preparing the application for approved research participation.

## Current Limitations

PhishSense remains an early-stage prototype.

The following features are not yet complete:

- Gamification and company-budget tracking
- Full results and history dashboards
- Pre-test and post-test workflows
- Formal research-group assignment
- Complete research evaluation
- Production deployment and security hardening

The current prototype demonstrates the core training experience and establishes the foundation for continued development.

## Version History

| Version | Milestone | Description |
|---|---|---|
| v0.1.0 | Milestone 1 | SQLite database foundation |
| v0.2.0 | Milestone 2 | User authentication and learner dashboard |
| v0.3.0 | Milestone 3 | Simulated inbox, classification, feedback, and response tracking |
| v0.4.0 | Milestone 4 | Supabase migration, adaptive/control workflows, matched pairs, and recurring-mistake tracking |

## Project Status

**Current Version: v0.4.0 (Milestone 4)**

Release metadata is recorded in [VERSION](VERSION); the corresponding annotated
Git tag is `v0.4.0`. See [release notes](releases/v0.4.0.md).

PhishSense is under active development as part of a master's capstone project.

The current application includes adaptive and fixed-control training, immediate feedback, recurring-mistake summaries, and progress recording. Future development will address research administration, evaluation, and other planned features.

## Milestone 4 submission materials

- [Research implementation update](research/Milestone4_Research_Progress.md)
- [Automated testing and submission validation](TESTING.md)
- [Adaptive and control rules](ADAPTIVE_TRAINING.md)
- [Recurring-mistake tracking](MISTAKE_TRACKING.md)
- [Scenario integration and capacity](SCENARIO_INTEGRATION.md)

Local recording helpers, walkthroughs containing synthetic login details, raw
unreviewed datasets, credentials, database files and generated artifacts are
intentionally excluded from version control. Never rerun migrations/imports on an
existing installation merely to demonstrate the application.
