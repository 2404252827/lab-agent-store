from pydantic import BaseModel
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str | None = None
    role: str = "student"
    phone: str | None = None
