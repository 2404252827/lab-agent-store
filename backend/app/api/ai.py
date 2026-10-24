from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.config import settings
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.pg_database import get_pg_db
from app.schemas.ai import ChatHistoryItem, ChatHistoryResponse, ChatRequest
from app.services import agent_service, chat_history_service

router = APIRouter(prefix="/ai", tags=["AI智能助手"])


@router.post("/chat")
async def chat(data: ChatRequest, user: User = Depends(get_current_user)):
    """AI 对话接口（非流式）

    请求体只传本次问题：{"content": "..."}
    对话历史由后端按当前登录用户读取。
    """
    res = await agent_service.chat(data, user)

    return Response.success(data=res)


@router.post("/chat/stream")
async def chat_stream(data: ChatRequest, user: User = Depends(get_current_user)):
    """AI 对话接口（SSE 流式）

    请求体：{"content": "..."}
    返回 text/event-stream，事件格式见 agent_service.stream_chat。
    """
    return StreamingResponse(
        agent_service.stream_chat(data, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/history")
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_pg_db),
):
    """获取当前登录用户的 AI 对话历史（按时间正序）

    只返回最近 CHAT_PAGE_LIMIT 条。用户身份来自 JWT，
    不接受任何请求参数，避免越权读取别人的对话。
    """
    records = await chat_history_service.list_messages(
        db, user.id, settings.CHAT_PAGE_LIMIT
    )

    return Response.success(
        data=ChatHistoryResponse(
            messages=[
                ChatHistoryItem(
                    role=record.role,  # type: ignore
                    content=record.content,
                    create_time=record.create_time,
                )
                for record in records
            ]
        )
    )


@router.delete("/history")
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_pg_db),
):
    """清空当前登录用户的 AI 对话历史"""

    deleted = await chat_history_service.clear(db, user.id)

    return Response.success(message=f"已清空 {deleted} 条对话记录")
