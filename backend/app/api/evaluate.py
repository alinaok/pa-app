from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ai.langgraph_evaluate import evaluate_graph
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/evaluate", tags=["evaluate"])

class EvaluateRequest(BaseModel):
    start_date: date
    end_date: date

class EvaluateResponse(BaseModel):
    summary: str

@router.post("/", response_model=EvaluateResponse)
def evaluate_moods_symptoms(
    req: EvaluateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user), 
):
    # Run the analysis workflow
    state = {
        "user_id": user.id,
        "start_date": str(req.start_date),
        "end_date": str(req.end_date),
        "db": db,
        "mood_data": [],
        "symptom_data": [],
        "summary": {},
        "error": None,
    }
    result = evaluate_graph.invoke(state)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return EvaluateResponse(summary=result["summary"])