# PhishSense

**Version:** 0.3.0 — Milestone 3 Prototype  
**Status:** Active Development  
**Project Type:** Master's Capstone — Cybersecurity Awareness Training

## Project Overview

PhishSense is a browser-based phishing-awareness training application designed to help users recognize phishing emails through simulated workplace scenarios, interactive email classification, immediate educational feedback, and eventually adaptive learning.

The application is being developed using Python, Flask, SQLite, HTML, and CSS.

PhishSense aims to provide a more engaging alternative to traditional phishing-awareness quizzes by allowing learners to review simulated emails in a realistic corporate inbox.

The long-term objective is to evaluate whether adaptive phishing-awareness training can improve users' ability to recognize phishing attempts compared with non-adaptive training.

## Current Development Version

**PhishSense v0.3.0 — Milestone 3 Prototype**

This version introduces a functional phishing-awareness training workflow.

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
- SQLite storage of training scenarios, sessions, and learner responses

The adaptive learning algorithm, gamification features, and full results dashboard are planned for future development.

## Evercrest Group: Simulated Training Environment

PhishSense uses a fictional organization named **Evercrest Group** to provide a consistent workplace setting for its training scenarios.

Instead of answering isolated quiz questions, learners interact with a simulated employee inbox containing phishing and legitimate messages.

The inbox displays email senders, subject lines, and review statuses. Learners can select messages in their preferred order, classify each email, and receive immediate feedback.

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
- **SQLite:** Local relational database
- **SQL:** Database schema and queries
- **HTML:** Application interfaces
- **CSS:** Interface styling
- **Werkzeug:** Password hashing and verification
- **Visual Studio Code:** Development environment
- **Git and GitHub:** Version control

## Database Architecture

PhishSense uses four primary SQLite tables.

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

### Database Relationships

- One user can have multiple training sessions.
- One training session can contain multiple responses.
- Each training response references a training scenario.

Foreign-key relationships are used to maintain referential integrity.

## Application Workflow

The current training workflow follows these steps:

1. A learner creates an account or logs in.
2. The learner accesses the PhishSense dashboard.
3. The learner opens the Evercrest Group employee inbox.
4. The application presents ten training scenarios.
5. The learner selects an unread email.
6. The learner reviews the sender, subject, and message content.
7. The learner classifies the message as phishing or legitimate.
8. The learner provides a written explanation.
9. The learner selects a confidence rating.
10. The application records the response in SQLite.
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

The adaptive learning algorithm, control-group workflow, and full research evaluation process have not yet been implemented.

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
| `app.py` | Main Flask application |
| `schema.sql` | SQLite database schema |
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

## Local Setup

PhishSense is currently intended to run locally for development and testing.

### 1. Open the Project Directory

Open the PhishSense project in Visual Studio Code or a terminal.

### 2. Create a Python Virtual Environment

```bash
python3 -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python3 -m pip install flask
```

### 4. Initialize the Database

For a new local installation, create the SQLite database using:

```bash
sqlite3 phishsense.db < schema.sql
```

Verify that the database tables exist:

```bash
sqlite3 phishsense.db ".tables"
```

Do not rerun the schema initialization command against an existing database without reviewing its contents and creating a backup.

### 5. Import Training Scenarios

```bash
python3 import_scenarios.py
```

### 6. Start the Application

```bash
python3 app.py
```

Open the local address displayed by Flask, typically:

http://127.0.0.1:5000

The application currently uses a development configuration and is not intended for public deployment.

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

Further testing is needed for complete-session behavior, additional users, and future adaptive functionality.

## Planned Development

Future milestones will focus on:

1. Improving the realism and complexity of simulated email scenarios.
2. Introducing safe, realistic-looking links and attachment representations.
3. Implementing adaptive scenario selection.
4. Developing the non-adaptive control-group training workflow.
5. Adding pre-training and post-training assessments.
6. Developing the learner results dashboard.
7. Implementing training history and performance visualization.
8. Adding Evercrest Group gamification features.
9. Expanding application testing.
10. Preparing the application for approved research participation.

## Current Limitations

PhishSense remains an early-stage prototype.

The following features are not yet complete:

- Adaptive difficulty adjustment
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

## Project Status

**Current Version: v0.3.0 — Milestone 3 Prototype**

PhishSense is under active development as part of a master's capstone project.

The current application provides a functional phishing-awareness training workflow. Future development will expand the adaptive learning, research evaluation, and gamification components.