from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import auth, messages
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth & Messaging System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # بعداً محدودش کن
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS, ...
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(admin.router)