from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from uuid import UUID

def create_task(db: Session, task: TaskCreate, user_id: UUID):
    db_task = Task(**task.model_dump(), user_id=user_id,)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_all_tasks(db: Session) -> list[Task]:
    return db.query(Task).all()

def get_task(db: Session, task_id: UUID) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task_id: UUID, task_update: TaskUpdate) -> Task:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    for field, value in task_update.model_dump(exclude_unset=True).items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: UUID) -> bool:
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False