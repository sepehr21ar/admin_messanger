from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.database import engine
from app import models
from app.routers import auth, messages
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin
from app.core.security import hash_password


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
app = FastAPI(title="Auth & Messaging System")

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE users "
            "ADD COLUMN IF NOT EXISTS created_by_admin_id INTEGER REFERENCES users(id)"
        ))
        conn.execute(text(
            "ALTER TABLE messages "
            "ADD COLUMN IF NOT EXISTS attachment_filename VARCHAR(255)"
        ))
        conn.execute(text(
            "ALTER TABLE messages "
            "ADD COLUMN IF NOT EXISTS attachment_stored_filename VARCHAR(255)"
        ))
        conn.execute(text(
            "ALTER TABLE messages "
            "ADD COLUMN IF NOT EXISTS attachment_content_type VARCHAR(100)"
        ))
        admin_exists = conn.execute(
            text("SELECT 1 FROM users WHERE username = :username"),
            {"username": "admin"},
        ).first()
        if not admin_exists:
            conn.execute(
                text(
                    "INSERT INTO users (username, password_hash, role) "
                    "VALUES (:username, :password_hash, :role)"
                ),
                {
                    "username": "admin",
                    "password_hash": hash_password("admin123"),
                    "role": "admin",
                },
            )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS, ...
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
def front_login():
    return FileResponse(FRONTEND_DIR / "login.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
