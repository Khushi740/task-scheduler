from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.models import TaskStatus, TaskType

class TaskCreate(BaseModel):
    name: str
    task_type: TaskType
    action: str                          # "email" | "report" | "log" | "http" | "cleanup"
    payload: Optional[str] = None        # JSON string
    scheduled_at: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    max_retries: Optional[int] = 3
    webhook_url: Optional[str] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    webhook_url: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskResponse(BaseModel):
    id: int
    name: str
    task_type: TaskType
    action: str
    payload: Optional[str]
    scheduled_at: Optional[datetime]
    interval_seconds: Optional[int]
    cron_expression: Optional[str]
    status: TaskStatus
    retry_count: int
    max_retries: int
    webhook_url: Optional[str]
    result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True