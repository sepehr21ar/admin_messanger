from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.core.security import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 👥 لیست کاربران
@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active
        }
        for u in users
    ]


# ✉️ ارسال پیام (نسخه ساده)
@router.post("/send-message")
def send_message(
    user_id: int,
    message: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    user = db.query(models.User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    msg = models.Message(
        title="Admin Message",
        content=message,
        admin_id=db.query(models.User).filter_by(username=admin["sub"]).first().id
    )
    db.add(msg)
    db.commit()

    return {"message": "Message sent"}
