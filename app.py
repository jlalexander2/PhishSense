import sqlite3

from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Welcome to PhishSense!</h1>
    <p>Adaptive Phishing Awareness Training System</p>
    <a href="/register">Create an Account</a>
    """


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or len(password) < 8:
            return "Please complete all fields and use a password of at least 8 characters.", 400

        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        connection = sqlite3.connect("phishsense.db")

        try:
            connection.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash),
            )
            connection.commit()

        except sqlite3.IntegrityError:
            return "That username or email is already registered.", 400

        finally:
            connection.close()

        return """
        <h1>Registration Successful!</h1>
        <p>Your PhishSense account has been created.</p>
        <a href="/">Return to Homepage</a>
        """

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)