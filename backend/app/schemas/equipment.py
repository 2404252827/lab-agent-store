from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_IMAGE_PATH_LENGTH = 100


def strip_required_text(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("不能为空")

    return value


class EquipmentResponse(BaseModel):
    id: int
    lab_id: int
    lab_name: str | None = None
    name: str
    description: str | None = None
    img: str | None = None
    spec: str | None = None
    quantity: int
    status: int

    model_config = ConfigDict(from_attributes=True)


class EquipmentCreateRequest(BaseModel):
    lab_id: int
    name: str = Field(max_length=50)
    description: str | None = Field(None, max_length=500)
    img: str | None = Field(None, max_length=MAX_IMAGE_PATH_LENGTH)
    spec: str | None = Field(None, max_length=100)
    quantity: int = Field(1, ge=0, le=9999)
    status: int = Field(1, ge=0, le=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return strip_required_text(value)


class EquipmentUpdateRequest(BaseModel):
    lab_id: int | None = None
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)
    img: str | None = Field(None, max_length=MAX_IMAGE_PATH_LENGTH)
    spec: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=0, le=9999)
    status: int | None = Field(None, ge=0, le=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return value if value is None else strip_required_text(value)