
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "PHISHSENSE_SECRET_KEY",
    "development-only-change-before-deployment"
)

DATABASE = "phishsense.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    if "user_id" in session:
        return f"""
        <h1>Welcome to PhishSense!</h1>
        <p>You are successfully logged in.</p>
        <p><a href="/logout">Log Out</a></p>
        """

    return """
    <h1>Welcome to PhishSense!</h1>
    <p>Adaptive Phishing Awareness Training System</p>
    <p><a href="/register">Create an Account</a></p>
    <p><a href="/login">Log In</a></p>
    """

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
            return """
            <h1>Registration Failed</h1>
            <p>That username or email is already registered.</p>
            <a href="/register">Try Again</a>
            """

        finally:
            conn.close()

        return """
        <h1>Registration Successful!</h1>
        <p>Your PhishSense account has been created.</p>
        <p><a href="/login">Log In</a></p>
        <p><a href="/">Return to Homepage</a></p>
        """

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect(url_for("home"))

        return """
        <h1>Login Failed</h1>
        <p>Invalid email or password.</p>
        <a href="/login">Try Again</a>
        """

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
