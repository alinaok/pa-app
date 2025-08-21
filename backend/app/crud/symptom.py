from sqlalchemy.orm import Session
from uuid import UUID
from app.models.symptom import Symptom
from app.schemas.symptom import SymptomCreate, SymptomUpdate
from datetime import datetime, timezone


def create_symptom(db: Session, symptom: SymptomCreate, user_id: UUID) -> Symptom:
    db_symptom = Symptom(
        user_id=user_id,
        description=symptom.description,
        created_at=symptom.date or datetime.now(timezone.utc)
    )
    db.add(db_symptom)
    db.commit()
    db.refresh(db_symptom)
    return db_symptom


def get_all_symptoms(db: Session) -> list[Symptom]:
    return db.query(Symptom).all()


def get_symptom(db: Session, symptom_id: UUID) -> Symptom | None:
    return db.query(Symptom).filter(Symptom.id == symptom_id).first()


def get_symptoms_by_user(db: Session, user_id: UUID) -> list[Symptom]:
    return db.query(Symptom).filter(Symptom.user_id == user_id).all()


def update_symptom(db: Session, symptom_id: UUID, symptom_update: SymptomUpdate) -> Symptom | None:
    db_symptom = get_symptom(db, symptom_id)
    if not db_symptom:
        return None
    for field, value in symptom_update.model_dump(exclude_unset=True).items():
        setattr(db_symptom, field, value)
    db.commit()
    db.refresh(db_symptom)
    return db_symptom


def delete_symptom(db: Session, symptom_id: UUID) -> bool:
    db_symptom = get_symptom(db, symptom_id)
    if db_symptom:
        db.delete(db_symptom)
        db.commit()
        return True
    return False
