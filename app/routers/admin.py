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
    return db.query(models.User).filter_by(is_active=True).order_by(models.User.id.asc()).all()

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
        role=data.role,
        created_by_admin_id=admin.get("user_id")
    )
    db.add(user)
    db.commit()
    return {"message": "User created"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    admin_id = admin.get("user_id")
    if admin_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user = db.query(models.User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin" and user.created_by_admin_id != admin_id:
        raise HTTPException(
            status_code=403,
            detail="You can delete this admin only if you created this admin account"
        )

    user.is_active = False
    db.commit()
    return {"message": f"User #{user_id} deleted"}
