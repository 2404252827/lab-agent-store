from pymysql import IntegrityError
from sqlalchemy import func, select

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.schemas.lab import (
    LabCreateRequest,
    LabResponse,
    LabUpdateRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession


async def _lab_name_taken(
    db: AsyncSession, name: str, exclude_id: int | None = None
) -> bool:
    """判断实验室名称是否已被占用，exclude_id 用于更新时排除自身"""

    stmt = select(Lab.id).where(Lab.name == name)

    if exclude_id is not None:
        stmt = stmt.where(Lab.id != exclude_id)

    return await db.scalar(stmt.limit(1)) is not None


def _check_time_range(open_time: str | None, close_time: str | None) -> None:
    """ "HH:MM" 零补齐后可直接按字符串比较，任一侧为空则不校验"""

    if open_time and close_time and close_time <= open_time:
        raise BusinessException(message="结束时间需要晚于开放时间")


async def get_lab_page_list(
    db: AsyncSession, page: int, page_size: int, keyword: str | None = None
):
    keyword = keyword.strip() if keyword else None

    stmt = select(Lab)
    count_stmt = select(func.count(Lab.id))

    if keyword:
        stmt = stmt.where(Lab.name.ilike(f"%{keyword}%"))
        count_stmt = count_stmt.where(Lab.name.ilike(f"%{keyword}%"))

    stmt = stmt.order_by(Lab.id.desc())
    stmt = stmt.offset(offset=(page - 1) * page_size).limit(page_size)

    result_page = await db.execute(stmt)
    items = result_page.scalars().all()
    total = await db.scalar(count_stmt)

    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items], total=total
    )


async def create_lab(data: LabCreateRequest, db: AsyncSession):
    if await _lab_name_taken(db, data.name):
        raise BusinessException(message="实验室已存在，请勿重复添加")

    _check_time_range(data.open_time, data.close_time)

    new_lab = Lab(**data.model_dump())

    db.add(new_lab)
    try:
        await db.commit()
    except IntegrityError:
        # 应用层检查和真正写入之间还是可能被别人插队，构建唯一索引捕获异常做回滚
        await db.rollback()
        raise BusinessException(message="实验室已存在，请勿重复添加")
    await db.refresh(new_lab)
    return LabResponse.model_validate(new_lab)


async def update_lab(lab_id: int, data: LabUpdateRequest, db: AsyncSession):
    result = await db.execute(select(Lab).where(Lab.id == lab_id))
    lab = result.scalar_one_or_none()

    if not lab:
        raise BusinessException(message="实验室不存在")

    data_dict = data.model_dump(exclude_none=True)

    if "name" in data_dict and await _lab_name_taken(
        db, data_dict["name"], exclude_id=lab_id
    ):
        raise BusinessException(message="实验室名称已被其他实验室占用")

    _check_time_range(
        data_dict.get("open_time", lab.open_time),
        data_dict.get("close_time", lab.close_time),
    )

    for field, value in data_dict.items():
        setattr(lab, field, value)

    await db.commit()
    await db.refresh(lab)

    return LabResponse.model_validate(lab)


async def delete_lab(lab_id: int, db: AsyncSession):
    result = await db.execute(select(Lab).where(Lab.id == lab_id))
    lab = result.scalar_one_or_none()

    if not lab:
        raise BusinessException(message="实验室不存在")

    result = await db.execute(select(Equipment).where(Equipment.lab_id == lab_id))
    exist = result.scalars().all()

    if exist:
        raise BusinessException(message="删除实验室失败，请先删除实验室设备")

    # 有预约记录的实验室不能删除，否则外键约束会直接抛 IntegrityError
    result = await db.execute(select(Reservation).where(Reservation.lab_id == lab_id))
    reserved = result.scalars().all()

    if reserved:
        raise BusinessException(message="删除实验室失败，请先处理该实验室的预约记录")

    await db.delete(lab)
    await db.commit()
