import re

from pydantic import BaseModel, Field, field_validator, ConfigDict

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
TIME_PATTERN_DATE = re.compile(r"^(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def check_time_text(value: str) -> str:
    if not TIME_PATTERN.match(value):
        raise ValueError("时间格式应为 HH:MM")

    return value


def check_date_text(value: str) -> str:
    if not TIME_PATTERN_DATE.match(value):
        raise ValueError("日期格式应为 YYYY-MM-DD")

    return value


class ReservationCreateRequest(BaseModel):
    lab_id: int
    date: str
    start_time: str
    end_time: str
    remark: str | None = Field(None, max_length=255)
    status: int = Field(0, ge=0, le=3)

    @field_validator("date")
    def validate_date(cls, value: str) -> str:
        return check_date_text(value)

    @field_validator("start_time", "end_time")
    def validate_time(cls, value: str) -> str:
        return check_time_text(value)


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    username: str | None = None
    nickname: str | None = None
    lab_id: int
    lab_name: str | None = None
    date: str
    start_time: str
    end_time: str
    remark: str | None = Field(None, max_length=255)
    status: int = Field(0, ge=0, le=3)

    model_config = ConfigDict(from_attributes=True)


class AuditReservationRequest(BaseModel):
    status: int
