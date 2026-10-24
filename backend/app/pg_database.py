from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 对话历史库：写少读多，连接池不用开太大
pg_engine = create_async_engine(
    settings.PG_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    # 避免空闲连接被 PostgreSQL / 网络设备断开后拿到坏连接
    pool_recycle=1800,
)

PgSessionFactory = async_sessionmaker(
    bind=pg_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class PgBase(DeclarativeBase):
    """对话历史库的基类，和业务库的 Base 完全独立"""


async def get_pg_db():
    """FastAPI 依赖：请求级 PG 会话。

    这里不自动 commit，写操作由 service 显式提交 ——
    和业务库 get_db 的约定保持一致。
    """

    async with PgSessionFactory() as session:
        yield session
