from typing import Any

from pydantic import BaseModel


class Response(BaseModel):
    code: int
    message: str
    data: Any = None

    @classmethod
    def success(cls, message: str = "响应成功", data: Any = None):
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 500, message: str = "响应失败", data: Any = None):
        return cls(code=code, message=message, data=data)


class PageResponse(BaseModel):
    list: Any = []
    total: int | None = None
