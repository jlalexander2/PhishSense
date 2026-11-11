PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_scenarios (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,

    sender_name TEXT NOT NULL,
    sender_email TEXT NOT NULL,

    subject TEXT NOT NULL,
    email_body TEXT NOT NULL,

    is_phishing INTEGER NOT NULL
        CHECK (is_phishing IN (0, 1)),

    difficulty_level TEXT NOT NULL
        CHECK (
            difficulty_level IN (
                'beginner',
                'intermediate',
                'advanced'
            )
        ),

    explanation TEXT NOT NULL,

    phishing_intent TEXT,
    phishing_technique TEXT,
    target_category TEXT,
    source_id TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    session_type TEXT NOT NULL
        CHECK (
            session_type IN (
                'pre_test',
                'training',
                'post_test'
            )
        ),

    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TEXT,

    current_difficulty TEXT NOT NULL DEFAULT 'intermediate'
        CHECK (
            current_difficulty IN (
                'beginner',
                'intermediate',
                'advanced'
            )
        ),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS training_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    scenario_id INTEGER NOT NULL,

    user_answer INTEGER NOT NULL
        CHECK (user_answer IN (0, 1)),

    is_correct INTEGER NOT NULL
        CHECK (is_correct IN (0, 1)),

    reasoning TEXT,

    confidence_level INTEGER NOT NULL
        CHECK (confidence_level BETWEEN 1 AND 5),

    response_time REAL NOT NULL
        CHECK (response_time >= 0),

    difficulty_at_response TEXT NOT NULL
        CHECK (
            difficulty_at_response IN (
                'beginner',
                'intermediate',
                'advanced'
            )
        ),

    answered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id)
        REFERENCES training_sessions(session_id),

    FOREIGN KEY (scenario_id)
        REFERENCES training_scenarios(scenario_id)
);