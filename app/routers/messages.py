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
        
@router.get("/sent")
def sent_messages(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    admin_user = db.query(models.User).filter_by(username=admin["sub"]).first()
    msgs = db.query(models.Message).filter_by(admin_id=admin_user.id).all()

    result = []
    for m in msgs:
        receivers = [
            {"id": r.user.id, "username": r.user.username}
            for r in m.recipients
        ]
        result.append({
            "id": m.id,
            "title": m.title,
            "content": m.content,
            "created_at": m.created_at,
            "receivers": receivers,
            "sender": m.admin.username  # 👈 اضافه شد
        })
    return result





@router.post("/send")
def send_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    admin_user = db.query(models.User).filter_by(username=admin["sub"]).first()

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
    u = db.query(models.User).filter_by(username=user["sub"]).first()

    recs = db.query(models.MessageRecipient).filter_by(user_id=u.id).all()

    return [
        {
            "id": r.message.id,
            "title": r.message.title,
            "sender": r.message.admin.username,  # 👈 فرستنده
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
    u = db.query(models.User).filter_by(username=user["sub"]).first()

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
    "sender": rec.message.admin.username,  # 👈
    "is_read": rec.is_read
}

@router.post("/{message_id}/read")
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    u = db.query(models.User).filter_by(username=user["sub"]).first()

    rec = db.query(models.MessageRecipient).filter_by(
        user_id=u.id,
        message_id=message_id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Message not found")

    rec.is_read = True
    db.commit()

    return {"message": "Marked as read"}
