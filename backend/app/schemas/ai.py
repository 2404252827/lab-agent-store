from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)


class ChatResponse(BaseModel):
    content: str


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    create_time: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatHistoryItem]
