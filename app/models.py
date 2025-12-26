from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(10), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages_sent = relationship("Message", back_populates="admin")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    admin_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User", back_populates="messages_sent")
    recipients = relationship("MessageRecipient", back_populates="message")


class MessageRecipient(Base):
    __tablename__ = "message_recipients"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_read = Column(Boolean, default=False)

    message = relationship("Message", back_populates="recipients")
