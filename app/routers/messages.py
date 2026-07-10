from datetime import datetime
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models
from app.core.security import get_current_admin, get_current_user
from app.database import SessionLocal

router = APIRouter(prefix="/messages", tags=["Messages"])

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads" / "message_attachments"


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


def attachment_payload(message: models.Message):
    if not message.attachment_stored_filename:
        return None
    return {
        "filename": message.attachment_filename,
        "content_type": message.attachment_content_type,
        "url": f"/messages/{message.id}/attachment",
    }


def parse_user_ids(user_ids: str):
    parsed_ids = []
    for raw_id in user_ids.split(","):
        raw_id = raw_id.strip()
        if not raw_id:
            continue
        try:
            parsed_ids.append(int(raw_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="User IDs must be numbers separated by commas")
    if not parsed_ids:
        raise HTTPException(status_code=400, detail="At least one recipient is required")
    return parsed_ids


def save_attachment(file: UploadFile | None):
    if not file or not file.filename:
        return None

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix
    stored_name = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / stored_name

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": original_name,
        "stored_filename": stored_name,
        "content_type": file.content_type,
    }


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
            "sender": participant_label(m.admin, m.admin_id),
            "attachment": attachment_payload(m),
        })
    return result


@router.post("/send")
def send_message(
    title: str = Form(...),
    content: str = Form(...),
    user_ids: str = Form(...),
    attachment: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    admin_user = db.query(models.User).filter_by(id=admin.get("user_id"), is_active=True).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin not found")

    recipient_ids = parse_user_ids(user_ids)
    if admin_user.id in recipient_ids:
        raise HTTPException(status_code=400, detail="You cannot send a message to yourself")

    active_user_ids = {
        row.id
        for row in db.query(models.User.id).filter(
            models.User.id.in_(recipient_ids),
            models.User.is_active.is_(True),
        ).all()
    }
    missing_user_ids = [uid for uid in recipient_ids if uid not in active_user_ids]
    if missing_user_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Users not found or deleted: {', '.join(map(str, missing_user_ids))}",
        )

    attachment_data = save_attachment(attachment)
    msg = models.Message(
        title=title,
        content=content,
        admin_id=admin_user.id,
        attachment_filename=attachment_data["filename"] if attachment_data else None,
        attachment_stored_filename=attachment_data["stored_filename"] if attachment_data else None,
        attachment_content_type=attachment_data["content_type"] if attachment_data else None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    for uid in recipient_ids:
        db.add(models.MessageRecipient(message_id=msg.id, user_id=uid))
    db.commit()
    return {"message": "Message sent", "id": msg.id, "attachment": attachment_payload(msg)}


@router.get("/inbox")
def inbox(db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    recs = db.query(models.MessageRecipient).filter_by(user_id=u.id).all()
    return [
        {
            "id": r.message.id,
            "title": r.message.title,
            "sender": participant_label(r.message.admin, r.message.admin_id),
            "created_at": r.message.created_at,
            "is_read": r.is_read,
            "attachment": attachment_payload(r.message),
        }
        for r in recs
    ]


@router.get("/{message_id}")
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    rec = db.query(models.MessageRecipient).filter_by(
        user_id=u.id,
        message_id=message_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Message not found")

    return {
        "id": rec.message.id,
        "title": rec.message.title,
        "content": rec.message.content,
        "sender": participant_label(rec.message.admin, rec.message.admin_id),
        "created_at": rec.message.created_at,
        "is_read": rec.is_read,
        "attachment": attachment_payload(rec.message),
    }


@router.get("/{message_id}/attachment")
def download_attachment(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    message = db.query(models.Message).filter_by(id=message_id).first()
    if not message or not message.attachment_stored_filename:
        raise HTTPException(status_code=404, detail="Attachment not found")

    user_id = user.get("user_id")
    can_download = user.get("role") == "admin" and message.admin_id == user_id
    if not can_download:
        can_download = db.query(models.MessageRecipient).filter_by(
            message_id=message_id,
            user_id=user_id,
        ).first() is not None
    if not can_download:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = UPLOAD_DIR / message.attachment_stored_filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file missing")

    return FileResponse(
        path=file_path,
        filename=message.attachment_filename or file_path.name,
        media_type=message.attachment_content_type or "application/octet-stream",
    )


@router.post("/{message_id}/read")
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    u = db.query(models.User).filter_by(id=user.get("user_id"), is_active=True).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    rec = db.query(models.MessageRecipient).filter_by(
        user_id=u.id,
        message_id=message_id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Message not found")

    rec.is_read = True
    rec.read_at = datetime.utcnow()
    db.commit()

    return {"message": "Marked as read"}
