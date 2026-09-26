from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Handle authentication operations for users."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository()

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.user_repository.get_by_username(self.db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
