from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.scheduler import schedule_task, scheduler

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    task = Task(**{k: v for k, v in payload.items() if v is not None})
    db.add(task)
    db.commit()
    db.refresh(task)
    schedule_task(task)
    return task


@router.get("/", response_model=List[TaskResponse])
def list_tasks(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Task)
    if user_id is not None:
        q = q.filter(Task.user_id == user_id)
    return q.all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    schedule_task(task)     # reschedule with updated values
    return task


@router.delete("/{task_id}", response_model=TaskResponse)
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.cancelled
    db.commit()
    db.refresh(task)
    try:
        scheduler.remove_job(str(task_id))
    except Exception:
        pass
    return task