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
