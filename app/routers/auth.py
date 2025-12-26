from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.core.security import verify_password, create_access_token

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
    user = db.query(models.User).filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}
