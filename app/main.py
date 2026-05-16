from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.routes.tasks import router as task_router
from app.routes.auth import router as auth_router
from app.scheduler import scheduler

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()       # start APScheduler when app boots
    yield
    scheduler.shutdown()    # clean shutdown when app stops

app = FastAPI(
    title="Task Scheduler API",
    description="Schedule and automate background jobs via REST API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(task_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Task Scheduler API is running 🚀"}