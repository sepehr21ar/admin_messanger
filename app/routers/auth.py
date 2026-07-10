from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas.user import PasswordChange
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    password_needs_hash_upgrade,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ⚠️ مسیر /register غیرفعال شد، فقط login باقی مانده

@router.post("/login")
def login(username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=username, is_active=True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if password_needs_hash_upgrade(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    
    # ✅ اضافه کردن user_id به توکن
    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "user_id": user.id          # <-- این خط جدید
    })
    return {"access_token": token, "token_type": "bearer"}


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user = db.query(models.User).filter_by(
        id=current_user.get("user_id"),
        is_active=True
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
    if len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
