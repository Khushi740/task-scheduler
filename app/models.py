from sqlalchemy import Column, String, Integer, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class TaskStatus(str, enum.Enum):
    pending  = "pending"
    running  = "running"
    done     = "done"
    failed   = "failed"
    cancelled = "cancelled"

class TaskType(str, enum.Enum):
    one_time   = "one_time"
    recurring  = "recurring"
    cron       = "cron"

class Task(Base):
    __tablename__ = "tasks"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    task_type     = Column(Enum(TaskType), nullable=False)          # one_time / recurring / cron
    action        = Column(String(50), nullable=False)              # email / report / log / http / cleanup
    payload       = Column(Text, nullable=True)                     # JSON string with action details
    scheduled_at  = Column(DateTime, nullable=True)                 # for one_time tasks
    interval_seconds = Column(Integer, nullable=True)               # for recurring tasks
    cron_expression  = Column(String(100), nullable=True)           # for cron tasks
    status        = Column(Enum(TaskStatus), default=TaskStatus.pending)
    retry_count   = Column(Integer, default=0)
    max_retries   = Column(Integer, default=3)
    webhook_url   = Column(String(255), nullable=True)
    result        = Column(Text, nullable=True)                     # output or error message
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())