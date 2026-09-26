from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Repository for user retrieval and validation logic."""

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()
