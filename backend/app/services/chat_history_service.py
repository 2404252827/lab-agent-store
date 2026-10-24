"""AI 对话历史的读写。

隔离原则：
所有函数都必须接收 user_id，而 user_id 只能由接口层从 JWT（get_current_user）
里取。绝不接受请求体里传进来的用户标识。

会话由调用方管理：
- 接口层用 Depends(get_pg_db)
- agent_service 里每次读/写各开一个短会话，
  不在大模型调用的几秒里一直占着数据库连接
"""

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessageRecord

logger = logging.getLogger(__name__)


async def list_messages(
    db: AsyncSession, user_id: int, limit: int
) -> list[ChatMessageRecord]:
    """读取某个用户最近的 limit 条消息，按时间正序返回。

    先按 id 倒序取最近 N 条，再反转成「旧 → 新」，
    正好是送给大模型的顺序。
    """

    if limit <= 0:
        return []

    stmt = (
        select(ChatMessageRecord)
        .where(ChatMessageRecord.user_id == user_id)
        .order_by(ChatMessageRecord.id.desc())
        .limit(limit)
    )

    rows = list((await db.execute(stmt)).scalars().all())
    rows.reverse()

    return rows


async def append_exchange(
    db: AsyncSession, user_id: int, user_content: str, assistant_content: str
) -> None:
    """把一问一答写进同一个事务。

    放在同一个事务里，是为了避免出现「只存了问题、没存回答」的半截会话。
    """

    db.add_all(
        [
            ChatMessageRecord(user_id=user_id, role="user", content=user_content),
            ChatMessageRecord(
                user_id=user_id, role="assistant", content=assistant_content
            ),
        ]
    )

    await db.commit()


async def clear(db: AsyncSession, user_id: int) -> int:
    """删除某个用户的全部对话，返回删除条数"""

    result = await db.execute(
        delete(ChatMessageRecord).where(ChatMessageRecord.user_id == user_id)
    )
    await db.commit()

    return result.rowcount or 0