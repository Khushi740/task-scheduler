import json
import logging
import smtplib
import httpx
from datetime import datetime
from email.mime.text import MIMEText
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Task, TaskStatus
from app.webhook import send_webhook

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


# ─────────────────────────────────────────────
# ACTIONS
# ─────────────────────────────────────────────

def action_log(payload: dict) -> str:
    message = payload.get("message", "No message provided")
    logger.info(f"[LOG TASK] {message}")
    return f"Logged: {message}"


def action_report(payload: dict) -> str:
    filename = payload.get("filename", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    content  = payload.get("content", "Auto-generated report.")
    with open(filename, "w") as f:
        f.write(f"Report generated at {datetime.now()}\n\n{content}")
    return f"Report saved to {filename}"


def action_http(payload: dict) -> str:
    url     = payload.get("url")
    method  = payload.get("method", "GET").upper()
    body    = payload.get("body", {})
    with httpx.Client() as client:
        if method == "POST":
            response = client.post(url, json=body, timeout=10)
        else:
            response = client.get(url, timeout=10)
    return f"HTTP {method} {url} → {response.status_code}"


def action_email(payload: dict) -> str:
    smtp_host = payload.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(payload.get("smtp_port", 587))
    sender    = payload.get("sender")
    password  = payload.get("password")
    recipient = payload.get("recipient")
    subject   = payload.get("subject", "Scheduled Email")
    body      = payload.get("body", "This is a scheduled email.")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    return f"Email sent to {recipient}"


def action_cleanup(payload: dict) -> str:
    db: Session = SessionLocal()
    try:
        older_than_days = int(payload.get("older_than_days", 7))
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=older_than_days)
        deleted = db.query(Task).filter(
            Task.status == TaskStatus.done,
            Task.updated_at < cutoff
        ).delete()
        db.commit()
        return f"Cleaned up {deleted} completed tasks older than {older_than_days} days"
    finally:
        db.close()


ACTION_MAP = {
    "log":     action_log,
    "report":  action_report,
    "http":    action_http,
    "email":   action_email,
    "cleanup": action_cleanup,
}


# ─────────────────────────────────────────────
# JOB RUNNER
# ─────────────────────────────────────────────

async def run_task(task_id: int):
    db: Session = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status == TaskStatus.cancelled:
            return

        task.status = TaskStatus.running
        db.commit()

        payload = json.loads(task.payload) if task.payload else {}
        action_fn = ACTION_MAP.get(task.action)

        if not action_fn:
            raise ValueError(f"Unknown action: {task.action}")

        result = action_fn(payload)
        task.status  = TaskStatus.done
        task.result  = result
        logger.info(f"Task {task_id} completed: {result}")

    except Exception as e:
        task.retry_count += 1
        task.result = str(e)
        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.failed
            logger.error(f"Task {task_id} failed after {task.retry_count} retries: {e}")
        else:
            task.status = TaskStatus.pending
            logger.warning(f"Task {task_id} retry {task.retry_count}/{task.max_retries}")

    finally:
        db.commit()
        webhook_url = task.webhook_url
        task_status = task.status
        task_result = task.result
        db.close()

        if webhook_url:
            await send_webhook(webhook_url, {
                "task_id": task_id,
                "status":  task_status,
                "result":  task_result,
            })


# ─────────────────────────────────────────────
# SCHEDULE A TASK
# ─────────────────────────────────────────────

def schedule_task(task: Task):
    if task.task_type == "one_time":
        scheduler.add_job(
            run_task, DateTrigger(run_date=task.scheduled_at),
            args=[task.id], id=str(task.id), replace_existing=True
        )
    elif task.task_type == "recurring":
        scheduler.add_job(
            run_task, IntervalTrigger(seconds=task.interval_seconds),
            args=[task.id], id=str(task.id), replace_existing=True
        )
    elif task.task_type == "cron":
        scheduler.add_job(
            run_task, CronTrigger.from_crontab(task.cron_expression),
            args=[task.id], id=str(task.id), replace_existing=True
        )