from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.session import get_db
import app.crud.symptom
from app.schemas.symptom import SymptomCreate, SymptomUpdate, SymptomOut
from app.models.symptom import Symptom
from app.ai.mood_symptom_helper import generate_symptom_advice
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/symptoms", tags=["symptoms"])

# @router.post("/", response_model=SymptomOut, status_code=status.HTTP_201_CREATED)
# def create_symptom(symptom: SymptomCreate, db: Session = Depends(get_db)):
#     return app.crud.symptom.create_symptom(db, symptom)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_symptom_and_generate_advice(symptom: SymptomCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Save to DB
    created_symptom = app.crud.symptom.create_symptom(db, symptom, user_id=user.id)

    # 2. Generate advice based on the saved symptom's description
    advice = generate_symptom_advice(description=symptom.description)

    # 3. Return both DB object and advice
    return {
        "id": str(created_symptom.id),
        "description": created_symptom.description,
        "user_id": str(created_symptom.user_id),
        "created_at": str(created_symptom.created_at),
        "advice": advice,
    }


@router.get("/", response_model=List[SymptomOut])
def get_all_symptoms(db: Session = Depends(get_db)):
    return app.crud.symptom.get_all_symptoms(db)

@router.get("/{symptom_id}", response_model=SymptomOut)
def get_symptom(symptom_id: UUID, db: Session = Depends(get_db)):
    db_symptom = app.crud.symptom.get_symptom(db, symptom_id)
    if not db_symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    return db_symptom

@router.put("/{symptom_id}", response_model=SymptomOut)
def update_symptom(symptom_id: UUID, symptom_update: SymptomUpdate, db: Session = Depends(get_db)):
    db_symptom = app.crud.symptom.update_symptom(db, symptom_id, symptom_update)
    if not db_symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    return db_symptom

@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_symptom(symptom_id: UUID, db: Session = Depends(get_db)):
    success = app.crud.symptom.delete_symptom(db, symptom_id)
    if not success:
        raise HTTPException(status_code=404, detail="Symptom not found")
    