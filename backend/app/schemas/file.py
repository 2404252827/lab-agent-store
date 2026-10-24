from pydantic import BaseModel


class FileResponse(BaseModel):
    original_name: str
    disk_name: str
    size: int | None
    url: str
