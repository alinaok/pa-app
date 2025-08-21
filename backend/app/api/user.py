from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, List, Any
import app.crud.user
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.db.session import get_db
from datetime import datetime, timedelta
from app.models.mood import Mood
from app.schemas.mood import MoodOut
from app.models.symptom import Symptom
from app.schemas.symptom import SymptomOut
from app.core.security import create_access_token


router = APIRouter(prefix="/users", tags=["Users"])

# Registration endpoint
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = app.crud.user.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return app.crud.user.register_user(db, user)

# Login endpoint
@router.post("/login")
def login(
    email: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db)
):
    user = app.crud.user.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"user_id": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = app.crud.user.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return app.crud.user.create_user(db, user)

@router.get("/", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return app.crud.user.get_all_users(db)

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = app.crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = app.crud.user.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    success = app.crud.user.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return


@router.get("/{user_id}/history", response_model=Dict[str, List[Any]])
def get_user_history(
    user_id: UUID,
    period: str = Query("month", enum=["month", "year", "all"]),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    if period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    # Query moods
    mood_query = db.query(Mood).filter(Mood.user_id == user_id)
    # Query symptoms
    symptom_query = db.query(Symptom).filter(Symptom.user_id == user_id)

    if start_date:
        mood_query = mood_query.filter(Mood.created_at >= start_date)
        symptom_query = symptom_query.filter(Symptom.created_at >= start_date)

    moods = mood_query.order_by(Mood.created_at).all()
    symptoms = symptom_query.order_by(Symptom.created_at).all()

    # Use Pydantic models to serialize
    moods_out = [MoodOut.model_validate(m) for m in moods]
    symptoms_out = [SymptomOut.model_validate(s) for s in symptoms]

    return {
        "moods": moods_out,
        "symptoms": symptoms_out
    }