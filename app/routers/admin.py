from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas.user import UserCreate
from app.core.security import get_current_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    return db.query(models.User).all()

@router.post("/create-user")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    if db.query(models.User).filter_by(username=data.username).first():
        raise HTTPException(400, "Username exists")

    user = models.User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role
    )
    db.add(user)
    db.commit()
    return {"message": "User created"}
