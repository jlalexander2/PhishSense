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
The initial database schema has been implemented and tested. The browser interface, application logic, and adaptive training features are planned for subsequent development.