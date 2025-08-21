from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import app.crud.reminder
from app.schemas.reminder import ReminderCreate, ReminderOut
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from datetime import datetime
from app.models.reminder import Reminder

router = APIRouter(prefix="/reminders", tags=["reminders"])

# Create a reminder
@router.post("/", response_model=ReminderOut)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_reminder = Reminder(
        user_id=user.id,
        task_id=reminder.task_id,
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        method=reminder.method,
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

# Get reminders due by date/range
@router.get("/due", response_model=List[ReminderOut])
def get_reminders_due(
    due_by: datetime = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return app.crud.reminder.get_reminders_due_by_date(db, user_id=user.id, due_by=due_by)

# Delete a reminder
@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user.id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    return
