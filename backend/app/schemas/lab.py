import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 时间统一用 "HH:MM" 字符串存储，空字符串表示「未设置」（便于前端清空该字段）
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def strip_required_text(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("不能为空")

    return value


def check_time_text(value: str) -> str:
    if value == "":
        return value

    if not TIME_PATTERN.match(value):
        raise ValueError("时间格式应为 HH:MM")

    return value


class LabResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    img: str | None = None
    location: str | None = None
    capacity: int
    open_time: str | None = None
    close_time: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class LabCreateRequest(BaseModel):
    name: str = Field(max_length=50)
    description: str | None = Field(None, max_length=500)
    img: str | None = Field(None, max_length=100)
    location: str = Field(max_length=100)
    capacity: int = Field(0, ge=0, le=9999)
    open_time: str | None = None
    close_time: str | None = None
    status: int = Field(1, ge=0, le=1)

    @field_validator("name", "location")
    def validate_text(cls, value: str) -> str:
        return strip_required_text(value)

    @field_validator("open_time", "close_time")
    def validate_time(cls, value: str | None) -> str | None:
        return value if value is None else check_time_text(value)


class LabUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)
    img: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)
    capacity: int | None = Field(None, ge=0, le=9999)
    open_time: str | None = None
    close_time: str | None = None
    status: int | None = Field(None, ge=0, le=1)

    @field_validator("name", "location")
    def validate_text(cls, value: str | None) -> str | None:
        return value if value is None else strip_required_text(value)

    @field_validator("open_time", "close_time")
    def validate_time(cls, value: str | None) -> str | None:
        return value if value is None else check_time_text(value)
