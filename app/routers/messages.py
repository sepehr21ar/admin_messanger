from fastapi import APIRouter, Depends
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
            "title": r.message.title,
            "content": r.message.content,
            "is_read": r.is_read
        }
        for r in recs
    ]
