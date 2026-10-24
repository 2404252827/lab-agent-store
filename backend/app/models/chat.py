from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.pg_database import PgBase


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatMessageRecord(PgBase):
    """AI 对话历史（每个用户一条持续会话）

    注意：
    - 这张表在独立的 PostgreSQL 里，user_id 无法建跨库外键，
      隔离完全依赖接口层从 JWT 取到的 user_id。
    - 只存用户可见的问答文本，工具调用过程不落库。
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        # 最常用的查询是「按用户取最近 N 条」，复合索引正好覆盖
        Index("ix_chat_messages_user_id_id", "user_id", "id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="所属用户")
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="角色：user / assistant"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息正文")
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, comment="创建时间"
    )