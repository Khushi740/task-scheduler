from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserResponse
from app.models import User
import hashlib

router = APIRouter(tags=["Auth"]) 


def _hash_password(username: str, password: str) -> str:
    # simple salted sha256 (demo only)
    s = f"{username}|{password}"
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    pw_hash = _hash_password(data.username, data.password)
    user = User(username=data.username, password_hash=pw_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserResponse)
def login(data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    pw_hash = _hash_password(data.username, data.password)
    if pw_hash != user.password_hash:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return user
