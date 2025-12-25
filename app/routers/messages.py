from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app import models
from app.core.security import get_current_user, get_current_admin

router = APIRouter(prefix="/messages", tags=["Messages"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
def get_active_users(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    users = db.query(models.User).filter_by(is_active=True, role="user").all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "created_at": u.created_at.isoformat()
        })
    return result

@router.post("/send")
def send_message(title: str, content: str, user_ids: List[int], db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    # پیام جدید بساز
    message = models.Message(
        title=title,
        content=content,
        admin_id=db.query(models.User).filter_by(username=admin["sub"]).first().id
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # تعیین گیرندگان
    for uid in user_ids:
        user = db.query(models.User).filter_by(id=uid, is_active=True).first()
        if not user:
            continue
        recipient = models.MessageRecipient(
            message_id=message.id,
            user_id=user.id
        )
        db.add(recipient)
    db.commit()
    return {"message": f"Message sent to {len(user_ids)} users"}


@router.get("/inbox")
def inbox(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(models.User).filter_by(username=current_user["sub"]).first()
    recipients = db.query(models.MessageRecipient).filter_by(user_id=user.id).all()

    result = []
    for r in recipients:
        msg = db.query(models.Message).filter_by(id=r.message_id).first()
        result.append({
            "id": msg.id,
            "title": msg.title,
            "content": msg.content,
            "is_read": r.is_read,
            "read_at": r.read_at
        })
    return result

@router.post("/{message_id}/read")
def mark_as_read(message_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(models.User).filter_by(username=current_user["sub"]).first()
    recipient = db.query(models.MessageRecipient).filter_by(user_id=user.id, message_id=message_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Message not found")

    recipient.is_read = True
    from datetime import datetime
    recipient.read_at = datetime.utcnow()
    db.commit()
    return {"message": "Marked as read"}
