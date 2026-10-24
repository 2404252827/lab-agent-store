from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings
from datetime import datetime
from sqlalchemy import DateTime

# 创建异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL, echo=False, pool_pre_ping=True
)
# 创建会话工厂
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


# 依赖注入函数，注入接口
async def get_db():
    async with AsyncSessionFactory() as session:
        yield session
        # 在这里取消掉commit,因为有写操作会在具体的接口中进行提交，避免读操作也会在yield之后提交一次
        # await session.commit()


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键ID"
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
