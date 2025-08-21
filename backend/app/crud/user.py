from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password

def register_user(db: Session, user: UserCreate) -> User:
    hashed_pw = hash_password(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_all_users(db: Session) -> list[User]:
    return db.query(User).all()

def get_user(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def update_user(db: Session, user_id: UUID, user_update: UserUpdate) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in user_update.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user
    return None

def delete_user(db: Session, user_id: UUID) -> bool:
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
