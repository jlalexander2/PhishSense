# PhishSense
PhishSense is a browser-based cybersecurity awareness training project designed to help users recognize phishing emails through simulated email scenarios, immediate feedback, and performance-based difficulty adjustments.

# Milestone 1 (T1): Database Foundation
This milestone establishes the initial SQLite database structure for PhishSense.

# Implemented Components
- `users`: Stores user account information.
- `training_scenarios`: Stores simulated phishing and legitimate email scenarios.
- `training_sessions`: Tracks pre-tests, training sessions, and post-tests.
- `training_responses`: Records user answers, accuracy, confidence levels, response times, and scenario difficulty.

# Database Relationships
- One user can have multiple training sessions.
- One training session can have multiple responses.
- Each response references one training scenario.

# Technologies
- SQLite
- SQL
- Visual Studio Code

# Setup
Run the following command in the project directory:

```bash
sqlite3 phishsense.db < schema.sql
```

Verify the tables:

```bash
sqlite3 phishsense.db ".tables"
```

# Testing Completed
- Successfully created all four database tables.
- Verified foreign-key enforcement using invalid record inserts.
- Confirmed no existing foreign-key violations.
- Passed SQLite database integrity check (`ok`).
- Confirmed temporary test records were rolled back.

# Current Status

## Milestone 1: Database Foundation
- Created and tested the SQLite database schema.
- Implemented tables for users, training scenarios, sessions, and responses.
- Verified database integrity and foreign-key relationships.

## Milestone 2: User Authentication and Dashboard
- Created a Flask-based web application.
- Implemented user registration with SQLite database integration.
- Added secure password hashing.
- Implemented user login and logout functionality.
- Added session-based authentication.
- Created a personalized learner dashboard.
- Added placeholder pages for training, results, and training history.
- Verified that protected pages redirect unauthenticated users to login.
- Tested application navigation and authentication functionality.

## Planned Development
- Implement simulated phishing email scenarios.
- Add learner responses and immediate feedback.
- Develop adaptive difficulty adjustments.
- Track training performance and session history.
- Implement pre-training and post-training assessments.