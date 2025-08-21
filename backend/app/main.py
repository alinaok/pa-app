from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import user, task, reminder, mood, symptom, evaluate, rag

app = FastAPI()

# allow CORS (Cross-Origin Resource Sharing) for requests from your frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(task.router)
app.include_router(reminder.router)
app.include_router(mood.router)
app.include_router(symptom.router)
app.include_router(evaluate.router)
app.include_router(rag.router)