# file: update_passwords.py

from app.database import SessionLocal
from app.models import User
from app.core.security import hash_password

def update_all_passwords():
    db = SessionLocal()
    users = db.query(User).all()
    
    for user in users:
        
        if not user.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            print(f"Updating password for user: {user.username}")
            user.password_hash = hash_password(user.password_hash)
    
    db.commit()
    db.close()
    print("✅ All passwords updated to bcrypt hash!")

if __name__ == "__main__":
    update_all_passwords()
