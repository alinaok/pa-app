from sqlalchemy.orm import Session
from uuid import UUID
from app.models.mood import Mood
from app.schemas.mood import MoodCreate, MoodUpdate
from datetime import datetime, timezone


def create_mood(db: Session, mood: MoodCreate, user_id: UUID) -> Mood:
    db_mood = Mood(
        user_id=user_id,
        description=mood.description,
        mood_type=mood.mood_type,
        intensity=mood.intensity,
        created_at=mood.date or datetime.now(timezone.utc)
    )
    db.add(db_mood)
    db.commit()
    db.refresh(db_mood)
    return db_mood


def get_all_moods(db: Session) -> list[Mood]:
    return db.query(Mood).all()


def get_mood(db: Session, mood_id: UUID) -> Mood | None:
    return db.query(Mood).filter(Mood.id == mood_id).first()


def get_moods_by_user(db: Session, user_id: UUID) -> list[Mood]:
    return db.query(Mood).filter(Mood.user_id == user_id).all()


def update_mood(db: Session, mood_id: UUID, mood_update: MoodUpdate) -> Mood | None:
    db_mood = get_mood(db, mood_id)
    if not db_mood:
        return None
    for field, value in mood_update.model_dump(exclude_unset=True).items():
        setattr(db_mood, field, value)
    db.commit()
    db.refresh(db_mood)
    return db_mood


def delete_mood(db: Session, mood_id: UUID) -> bool:
    db_mood = get_mood(db, mood_id)
    if db_mood:
        db.delete(db_mood)
        db.commit()
        return True
    return False
