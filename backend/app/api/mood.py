from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import app.crud.mood
from app.schemas.mood import MoodCreate, MoodUpdate, MoodOut
from app.db.session import get_db
from app.ai.mood_symptom_helper import generate_pep_talk, generate_affirmation, generate_daily_quote
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/moods", tags=["moods"])

# @router.post("/", response_model=MoodOut, status_code=status.HTTP_201_CREATED)
# def create_mood(mood: MoodCreate, db: Session = Depends(get_db)):
#     return app.crud.mood.create_mood(db, mood)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mood_and_generate(mood_in: MoodCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Save mood to DB
    mood = app.crud.mood.create_mood(db, mood_in, user_id=user.id)

    # 2. Immediately generate pep talk and affirmation based on the input (no DB lookup)
    pep_talk = generate_pep_talk(
        mood_in.mood_type.value if mood_in.mood_type else None, 
        mood_in.description or "", 
        mood_in.intensity
    )
    affirmation = generate_affirmation(
        mood_in.mood_type.value if mood_in.mood_type else None, 
        mood_in.description or ""
    )

    # 3. Return mood ID + generated messages
    return {
        "id": mood.id,
        "pep_talk": pep_talk,
        "affirmation": affirmation
    }


@router.get("/", response_model=List[MoodOut])
def get_all_moods(db: Session = Depends(get_db)):
    return app.crud.mood.get_all_moods(db)

@router.get("/{mood_id}", response_model=MoodOut)
def get_mood(mood_id: UUID, db: Session = Depends(get_db)):
    db_mood = app.crud.mood.get_mood(db, mood_id)
    if not db_mood:
        raise HTTPException(status_code=404, detail="Mood not found")
    return db_mood

@router.put("/{mood_id}", response_model=MoodOut)
def update_mood(mood_id: UUID, mood_update: MoodUpdate, db: Session = Depends(get_db)):
    db_mood = app.crud.mood.update_mood(db, mood_id, mood_update)
    if not db_mood:
        raise HTTPException(status_code=404, detail="Mood not found")
    return db_mood

@router.delete("/{mood_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mood(mood_id: UUID, db: Session = Depends(get_db)):
    success = app.crud.mood.delete_mood(db, mood_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mood not found")
    return None

@router.get("/daily-quote")
def get_daily_quote():
    """Generate a daily motivational quote"""
    try:
        quote = generate_daily_quote()
        return {"quote": quote}
    except Exception as e:
        # Fallback quote if AI generation fails
        fallback_quotes = [
            "Every day is a new opportunity to be better than yesterday.",
            "You are capable of amazing things.",
            "Your potential is limitless.",
            "Today is your day to shine.",
            "Believe in yourself and all that you are."
        ]
        import random
        return {"quote": random.choice(fallback_quotes)}
