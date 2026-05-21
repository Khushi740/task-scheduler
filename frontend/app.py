from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "taskscheduler_secret_123"

API_BASE = "http://127.0.0.1:8000"

# Simple credentials — change as you like
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"


# ── AUTH DECORATOR ──
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── LOGIN / LOGOUT ──
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session["logged_in"] = True
            session["username"]  = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── DASHBOARD ──
@app.route("/")
@login_required
def dashboard():
    try:
        response = requests.get(f"{API_BASE}/tasks")
        tasks = response.json()
    except:
        tasks = []

    total     = len(tasks)
    pending   = len([t for t in tasks if t["status"] == "pending"])
    done      = len([t for t in tasks if t["status"] == "done"])
    failed    = len([t for t in tasks if t["status"] == "failed"])
    running   = len([t for t in tasks if t["status"] == "running"])
    cancelled = len([t for t in tasks if t["status"] == "cancelled"])

    return render_template("dashboard.html",
        tasks=tasks, total=total, pending=pending,
        done=done, failed=failed, running=running, cancelled=cancelled
    )


@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():
    error = None
    if request.method == "POST":
        payload = {
            "name":             request.form.get("name"),
            "task_type":        request.form.get("task_type"),
            "action":           request.form.get("action"),
            "payload":          request.form.get("payload") or None,
            "scheduled_at":     request.form.get("scheduled_at") or None,
            "interval_seconds": int(request.form["interval_seconds"]) if request.form.get("interval_seconds") else None,
            "cron_expression":  request.form.get("cron_expression") or None,
            "max_retries":      int(request.form.get("max_retries", 3)),
            "webhook_url":      request.form.get("webhook_url") or None,
        }
        try:
            res = requests.post(f"{API_BASE}/tasks", json=payload)
            if res.status_code == 200:
                return redirect(url_for("dashboard"))
            else:
                error = res.json().get("detail", "Something went wrong")
        except Exception as e:
            error = str(e)

    return render_template("create_task.html", error=error)


@app.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    try:
        res  = requests.get(f"{API_BASE}/tasks/{task_id}")
        task = res.json()
    except:
        task = None
    return render_template("task_detail.html", task=task)


@app.route("/tasks/<int:task_id>/cancel", methods=["POST"])
@login_required
def cancel_task(task_id):
    requests.delete(f"{API_BASE}/tasks/{task_id}")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)