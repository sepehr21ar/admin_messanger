from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas.message import MessageCreate
from app.core.security import get_current_admin, get_current_user

router = APIRouter(prefix="/messages", tags=["Messages"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def participant_label(user, user_id: int | None):
    if user and user.is_active:
        return user.username
    if user_id:
        return f"Deleted user #{user_id}"
    return "Deleted user"
        
@router.get("/sent")
def sent_messages(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    admin_user = db.query(models.User).filter_by(id=admin.get("user_id"), is_active=True).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin not found")
    msgs = db.query(models.Message).filter_by(admin_id=admin_user.id).all()

    result = []
    for m in msgs:
        receivers = [
            {"id": r.user_id, "username": participant_label(r.user, r.user_id)}
            for r in m.recipients
        ]
        result.append({
            "id": m.id,
            "title": m.title,
            "content": m.content,
            "created_at": m.created_at,
            "receivers": receivers,
            "sender": participant_label(m.admin, m.admin_id)
        })
    return result





@router.post("/send")
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    admin_user = db.query(models.User).filter_by(id=admin.get("user_id"), is_active=True).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # اعتبارسنجی: جلوگیری از ارسال پیام به خود ادمین
    if admin_user.id in data.user_ids:
        raise HTTPException(status_code=400, detail="شما نمی‌توانید به خودتان پیام ارسال کنید")
    
    active_user_ids = {
        row.id
        for row in db.query(models.User.id).filter(
            models.User.id.in_(data.user_ids),
            models.User.is_active.is_(True)
        ).all()
    }
    missing_user_ids = [uid for uid in data.user_ids if uid not in active_user_ids]
    if missing_user_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Users not found or deleted: {', '.join(map(str, missing_user_ids))}"
        )

    msg = models.Message(
        title=data.title,
        content=data.content,
        admin_id=admin_user.id
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    for uid in data.user_ids:
        db.add(models.MessageRecipient(
            message_id=msg.id,
            user_id=uid
        ))
    db.commit()
    return {"message": "Message sent"}


@router.get("/inbox")
def inbox(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    recs = db.query(models.MessageRecipient).filter_by(user_id=u.id).all()

    return [
    {
        "id": r.message.id,
        "title": r.message.title,
        "sender": participant_label(r.message.admin, r.message.admin_id),
        "created_at": r.message.created_at,  # اضافه شود
        "is_read": r.is_read
    }
    for r in recs
]


@router.get("/{message_id}")
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    rec = db.query(models.MessageRecipient).filter_by(
        user_id=u.id,
        message_id=message_id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Message not found")

    return {
        "id": rec.message.id,
        "title": rec.message.title,
        "content": rec.message.content,
        "sender": participant_label(rec.message.admin, rec.message.admin_id),
        "created_at": rec.message.created_at,   # 👈 اضافه کردن این خط
        "is_read": rec.is_read
    }

@router.post("/{message_id}/read")
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    rec = db.query(models.MessageRecipient).filter_by(
        user_id=u.id,
        message_id=message_id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Message not found")

    rec.is_read = True
    rec.read_at = datetime.utcnow()
    db.commit()

    return {"message": "Marked as read"}
