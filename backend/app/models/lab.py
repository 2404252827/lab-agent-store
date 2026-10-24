from sqlalchemy import Integer, String

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column


class Lab(Base):
    __tablename__ = "labs"
    __table_args__ = {"comment": "实验室信息"}

    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, comment="名称"
    )
    description: Mapped[str | None] = mapped_column(String(500), comment="简介")
    img: Mapped[str | None] = mapped_column(String(100), comment="封面")
    location: Mapped[str] = mapped_column(String(100), comment="位置")
    capacity: Mapped[int] = mapped_column(Integer, comment="容量", default=0)
    open_time: Mapped[str | None] = mapped_column(String(20), comment="开放时间")
    close_time: Mapped[str | None] = mapped_column(String(20), comment="结束时间")
    status: Mapped[int] = mapped_column(
        Integer, comment="状态，0-关闭，1-开放", default=1
    )
