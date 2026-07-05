from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
