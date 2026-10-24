from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey

from app.models.lab import Lab
from app.models.user import User


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"comment": "实验室预约信息"}

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="预约者")
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), comment="被预约的实验室")
    date: Mapped[str] = mapped_column(String(20), comment="预约时间")
    start_time: Mapped[str] = mapped_column(String(20), comment="开始时间")
    end_time: Mapped[str] = mapped_column(String(20), comment="结束时间")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
    status: Mapped[int] = mapped_column(
        Integer, comment="0-待审核，1-同意，2-驳回，3-取消", default=0
    )

    user: Mapped[User] = relationship()
    lab: Mapped[Lab] = relationship()
