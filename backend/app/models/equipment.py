from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from app.database import Base
from app.models.lab import Lab


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = {"comment": "实验室设备"}

    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), comment="所属实验室")
    name: Mapped[str] = mapped_column(String(50), comment="设备名称")
    description: Mapped[str | None] = mapped_column(String(500), comment="说明")
    img: Mapped[str | None] = mapped_column(String(100), comment="展示")
    spec: Mapped[str | None] = mapped_column(String(100), comment="型号规格")
    quantity: Mapped[int] = mapped_column(Integer, comment="容量", default=1)
    status: Mapped[int] = mapped_column(
        Integer, comment="状态，0-维修，1-正常", default=1
    )

    lab: Mapped[Lab] = relationship()
