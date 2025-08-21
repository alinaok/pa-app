from sqlalchemy.orm import Session
from uuid import UUID
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate
from datetime import datetime

def create_reminder(db: Session, reminder: ReminderCreate, user_id: UUID) -> Reminder:
    db_reminder = Reminder(**reminder.model_dump(), user_id=user_id)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def get_reminders_due_by_date(db: Session, user_id: UUID, due_by: datetime) -> list[Reminder]:
    return db.query(Reminder).filter(
        Reminder.user_id == user_id,
        Reminder.remind_at <= due_by
    ).order_by(Reminder.remind_at).all()

def delete_reminder(db: Session, reminder_id: UUID) -> None:
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if db_reminder:
        db.delete(db_reminder)
        db.commit()
