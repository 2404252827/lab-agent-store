from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None
    status: int | None = None


class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str


class UserCreateRequest(BaseModel):
    username: str
    password: str = "111111"
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str = "student"
    status: int = 1
