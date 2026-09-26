import secrets

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using a strong bcrypt-based algorithm."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify user password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def generate_session_token() -> str:
    """Generate a secure random token for session tracking."""
    return secrets.token_urlsafe(32)
