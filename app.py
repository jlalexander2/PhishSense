import os
import sqlite3
import time
import secrets
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get(
    "PHISHSENSE_SECRET_KEY",
    "development-only-change-before-deployment"
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "phishsense.db"
)

SESSION_EMAIL_LIMIT = 10


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def login_required():
    return "user_id" in session


def get_reviewed_ids(conn, training_session_id):
    rows = conn.execute(
        """
        SELECT DISTINCT scenario_id
        FROM training_responses
        WHERE session_id = ?
        """,
        (training_session_id,)
    ).fetchall()

    return {row["scenario_id"] for row in rows}


def get_active_training_session(conn):
    training_session_id = session.get("training_session_id")

    if training_session_id is None:
        return None

    return conn.execute(
        """
        SELECT *
        FROM training_sessions
        WHERE session_id = ?
          AND user_id = ?
          AND session_type = 'training'
        """,
        (training_session_id, session["user_id"])
    ).fetchone()


def create_training_session(conn):
    scenarios = conn.execute(
        """
        SELECT scenario_id
        FROM training_scenarios
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (SESSION_EMAIL_LIMIT,)
    ).fetchall()

    scenario_ids = [row["scenario_id"] for row in scenarios]

    if not scenario_ids:
        return None

    cursor = conn.execute(
        """
        INSERT INTO training_sessions (
            user_id,
            session_type,
            current_difficulty
        )
        VALUES (?, 'training', 'intermediate')
        """,
        (session["user_id"],)
    )

    conn.commit()

    session["training_session_id"] = cursor.lastrowid
    session["training_scenario_ids"] = scenario_ids
    session.pop("active_scenario_id", None)
    session.pop("scenario_started_at", None)
    session.pop("active_form_token", None)

    return cursor.lastrowid


def get_training_scenario_ids():
    scenario_ids = session.get("training_scenario_ids", [])

    if not isinstance(scenario_ids, list):
        return []

    if not all(type(scenario_id) is int for scenario_id in scenario_ids):
        return []

    return scenario_ids


@app.route("/")
def home():
    if login_required():
        return (
            '<h1>Welcome to PhishSense!</h1>'
            '<p>You are successfully logged in.</p>'
            '<p><a href="/dashboard">Go to Dashboard</a></p>'
            '<p><a href="/logout">Log Out</a></p>'
        )

    return (
        '<h1>Welcome to PhishSense!</h1>'
        '<p>Adaptive Phishing Awareness Training System</p>'
        '<p><a href="/register">Create an Account</a></p>'
        '<p><a href="/login">Log In</a></p>'
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            return "All fields are required.", 400

        password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            return (
                '<h1>Registration Failed</h1>'
                '<p>That username or email is already registered.</p>'
                '<a href="/register">Try Again</a>'
            )

        finally:
            conn.close()

        return (
            '<h1>Registration Successful!</h1>'
            '<p>Your PhishSense account has been created.</p>'
            '<p><a href="/login">Log In</a></p>'
            '<p><a href="/">Return to Homepage</a></p>'
        )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        finally:
            conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return (
            '<h1>Login Failed</h1>'
            '<p>Invalid email or password.</p>'
            '<a href="/login">Try Again</a>'
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session.get("username", "Learner")
    )


@app.route("/inbox")
def inbox():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        training_session = get_active_training_session(conn)
        scenario_ids = get_training_scenario_ids()

        if (
            training_session is None
            or not scenario_ids
        ):
            training_session_id = create_training_session(conn)

            if training_session_id is None:
                return render_template(
                    "inbox.html",
                    username=session.get("username", "Learner"),
                    emails=[],
                    reviewed_ids=set(),
                    reviewed_count=0,
                    total_count=0,
                    progress_percent=0
                )

            training_session = get_active_training_session(conn)
            scenario_ids = get_training_scenario_ids()

        placeholders = ",".join("?" for _ in scenario_ids)

        emails = conn.execute(
            f"""
            SELECT *
            FROM training_scenarios
            WHERE scenario_id IN ({placeholders})
            """,
            scenario_ids
        ).fetchall()

        email_lookup = {
            email["scenario_id"]: email
            for email in emails
        }

        ordered_emails = [
            email_lookup[scenario_id]
            for scenario_id in scenario_ids
            if scenario_id in email_lookup
        ]

        reviewed_ids = get_reviewed_ids(
            conn,
            training_session["session_id"]
        )

        total_count = len(ordered_emails)
        reviewed_count = sum(
            1
            for email in ordered_emails
            if email["scenario_id"] in reviewed_ids
        )

        progress_percent = (
            round((reviewed_count / total_count) * 100)
            if total_count > 0
            else 0
        )

        if (
            total_count > 0
            and reviewed_count == total_count
            and training_session["completed_at"] is None
        ):
            conn.execute(
                """
                UPDATE training_sessions
                SET completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                  AND completed_at IS NULL
                """,
                (training_session["session_id"],)
            )
            conn.commit()

    finally:
        conn.close()

    return render_template(
        "inbox.html",
        username=session.get("username", "Learner"),
        emails=ordered_emails,
        reviewed_ids=reviewed_ids,
        reviewed_count=reviewed_count,
        total_count=total_count,
        progress_percent=progress_percent
    )


@app.route("/training", methods=["GET", "POST"])
def training():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        scenario_id = request.args.get(
            "scenario_id",
            type=int
        )

        if scenario_id is None:
            return redirect(url_for("inbox"))

        scenario_ids = get_training_scenario_ids()

        if scenario_id not in scenario_ids:
            return redirect(url_for("inbox"))

        conn = get_db_connection()

        try:
            training_session = get_active_training_session(conn)

            if (
                training_session is None
                or training_session["completed_at"] is not None
            ):
                return redirect(url_for("inbox"))

            reviewed_ids = get_reviewed_ids(
                conn,
                training_session["session_id"]
            )

            if scenario_id in reviewed_ids:
                return redirect(url_for("inbox"))

            scenario = conn.execute(
                """
                SELECT *
                FROM training_scenarios
                WHERE scenario_id = ?
                """,
                (scenario_id,)
            ).fetchone()

        finally:
            conn.close()

        if scenario is None:
            return redirect(url_for("inbox"))

        if session.get("active_scenario_id") != scenario_id:
            session["scenario_started_at"] = time.time()

        if not isinstance(
            session.get("scenario_started_at"),
            (int, float)
        ):
            session["scenario_started_at"] = time.time()

        session["active_scenario_id"] = scenario_id
        session["active_form_token"] = secrets.token_urlsafe(24)

        return render_template(
            "training.html",
            scenario=scenario,
            username=session.get("username", "Learner"),
            form_token=session["active_form_token"]
        )

    try:
        scenario_id = int(request.form.get("scenario_id", ""))
        user_answer = int(request.form.get("user_answer", ""))
        confidence_level = int(
            request.form.get("confidence_level", "")
        )

    except (ValueError, TypeError):
        return "Invalid training response.", 400

    reasoning = request.form.get("reasoning", "").strip()
    form_token = request.form.get("form_token", "")

    if user_answer not in (0, 1):
        return "Invalid classification.", 400

    if confidence_level not in range(1, 6):
        return "Confidence must be between 1 and 5.", 400

    if not reasoning:
        return "Please explain your classification.", 400

    if len(reasoning) > 5000:
        return "Your explanation is too long.", 400

    if scenario_id not in get_training_scenario_ids():
        return "This email is not part of your training session.", 400

    if session.get("active_scenario_id") != scenario_id:
        return "This training email is no longer active.", 400

    expected_token = session.get("active_form_token")

    if (
        not expected_token
        or not secrets.compare_digest(form_token, expected_token)
    ):
        return "Invalid or expired training form.", 400

    started_at = session.get("scenario_started_at")

    if not isinstance(started_at, (int, float)):
        return "Training start time is missing.", 400

    response_time = max(0.0, time.time() - started_at)

    conn = get_db_connection()

    try:
        training_session = get_active_training_session(conn)

        if (
            training_session is None
            or training_session["completed_at"] is not None
        ):
            return "This training session is no longer active.", 400

        reviewed_ids = get_reviewed_ids(
            conn,
            training_session["session_id"]
        )

        if scenario_id in reviewed_ids:
            return redirect(url_for("inbox"))

        scenario = conn.execute(
            """
            SELECT *
            FROM training_scenarios
            WHERE scenario_id = ?
            """,
            (scenario_id,)
        ).fetchone()

        if scenario is None:
            return "Training scenario not found.", 404

        is_correct = int(
            user_answer == scenario["is_phishing"]
        )

        conn.execute(
            """
            INSERT INTO training_responses (
                session_id,
                scenario_id,
                user_answer,
                is_correct,
                reasoning,
                confidence_level,
                response_time,
                difficulty_at_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                training_session["session_id"],
                scenario_id,
                user_answer,
                is_correct,
                reasoning,
                confidence_level,
                response_time,
                scenario["difficulty_level"]
            )
        )

        conn.commit()

    finally:
        conn.close()

    session.pop("active_scenario_id", None)
    session.pop("scenario_started_at", None)
    session.pop("active_form_token", None)

    return render_template(
        "training_feedback.html",
        scenario=scenario,
        is_correct=bool(is_correct),
        user_answer=user_answer,
        confidence_level=confidence_level,
        reasoning=reasoning
    )


@app.route("/results")
def results():
    if not login_required():
        return redirect(url_for("login"))

    return (
        '<h1>My Results</h1>'
        '<p>Your training results will appear here '
        'once the results dashboard is implemented.</p>'
        '<a href="/dashboard">Back to Dashboard</a>'
    )


@app.route("/history")
def history():
    if not login_required():
        return redirect(url_for("login"))

    return (
        '<h1>Training History</h1>'
        '<p>Your completed training sessions will appear here.</p>'
        '<a href="/dashboard">Back to Dashboard</a>'
    )


if __name__ == "__main__":
    app.run(debug=True)