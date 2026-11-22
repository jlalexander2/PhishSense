"""Small validation helpers; never transform stored learner answers or passwords."""
import re
import secrets

MAX_DATABASE_ID = 2_147_483_647
MAX_PASSWORD_LENGTH = 1024
MAX_USERNAME_LENGTH = 80
MAX_EMAIL_LENGTH = 254


def valid_email(value):
    # Conservative syntax check, not delivery or account-ownership verification.
    return (0 < len(value) <= MAX_EMAIL_LENGTH and
            re.fullmatch(r'[^\s@\x00-\x1f\x7f]+@[^\s@\x00-\x1f\x7f]+\.[^\s@\x00-\x1f\x7f]+', value) is not None)


def valid_registration(username, email, password):
    return (0 < len(username) <= MAX_USERNAME_LENGTH and
            not any(ord(c) < 32 or ord(c) == 127 for c in username) and
            valid_email(email) and 0 < len(password) <= MAX_PASSWORD_LENGTH and
            '\x00' not in password)


def database_id(value):
    """Bound identifiers before PostgreSQL parameter adaptation (INTEGER columns)."""
    try:
        result = int(value)
    except (ValueError, TypeError):
        return None
    return result if 0 < result <= MAX_DATABASE_ID else None


def tokens_match(actual, expected):
    # compare_digest(str, str) rejects non-ASCII input; untrusted forms must not 500.
    return (isinstance(actual, str) and isinstance(expected, str) and bool(expected)
            and secrets.compare_digest(actual.encode('utf-8'), expected.encode('utf-8')))
