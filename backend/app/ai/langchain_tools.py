# for database access and data fetching
from langchain.tools import tool
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.mood import Mood
from app.models.symptom import Symptom

@tool
def get_recent_moods(user_id: str, db: Session, days: int = 7) -> list:
    """
    Fetches the user's mood entries from the past N days.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    moods = db.query(Mood).filter(
        Mood.user_id == user_id,
        Mood.created_at >= cutoff
    ).order_by(Mood.created_at.desc()).all()
    return [{"mood_type": m.mood_type.value, "description": m.description, "created_at": m.created_at.isoformat()} for m in moods]


@tool
def get_recent_symptoms(user_id: str, db: Session, days: int = 14) -> list:
    """
    Fetch the user's symptoms from the last `days` days.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    symptoms = db.query(Symptom).filter(
        Symptom.user_id == user_id,
        Symptom.created_at >= cutoff
    ).order_by(Symptom.created_at.desc()).all()
    
    return [{
        "description": s.description,
        "intensity": s.intensity,
        "created_at": s.created_at.isoformat()
    } for s in symptoms]


@tool
def get_mood_and_symptom_history(user_id: str, start_date: str, end_date: str, db: Session) -> dict:
    """
    Fetches mood and symptom history for the user within the date range.
    Dates must be ISO format strings: YYYY-MM-DD
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    moods = db.query(Mood).filter(
        Mood.user_id == user_id,
        Mood.created_at >= start,
        Mood.created_at <= end
    ).order_by(Mood.created_at).all()

    symptoms = db.query(Symptom).filter(
        Symptom.user_id == user_id,
        Symptom.created_at >= start,
        Symptom.created_at <= end
    ).order_by(Symptom.created_at).all()

    return {
        "moods": [
            {
                "date": m.created_at.isoformat(),
                "type": m.mood_type.value if m.mood_type else "unknown",
                "description": m.description,
                "intensity": m.intensity
            } for m in moods
        ],
        "symptoms": [
            {
                "date": s.created_at.isoformat(),
                "description": s.description,
                "intensity": s.intensity
            } for s in symptoms
        ]
    }