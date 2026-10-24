from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentUpdateRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession


async def get_equipment_page_list(
    db: AsyncSession,
    page: int,
    page_size: int,
    keyword: str | None = None,
    lab_id: int | None = None,
):
    keyword = keyword.strip() if keyword else None

    # 异步会话里不能惰性加载关联，列表统一用 selectinload 预加载实验室
    stmt = select(Equipment).options(selectinload(Equipment.lab))
    count_stmt = select(func.count(Equipment.id))

    if lab_id:
        stmt = stmt.where(Equipment.lab_id == lab_id)
        count_stmt = count_stmt.where(Equipment.lab_id == lab_id)

    if keyword:
        stmt = stmt.where(Equipment.name.ilike(f"%{keyword}%"))
        count_stmt = count_stmt.where(Equipment.name.ilike(f"%{keyword}%"))

    stmt = stmt.order_by(Equipment.id.desc())
    stmt = stmt.offset(offset=(page - 1) * page_size).limit(page_size)

    result_page = await db.execute(stmt)
    items = result_page.scalars().all()
    total = await db.scalar(count_stmt)

    result_list = []
    for item in items:
        equipment_data = EquipmentResponse.model_validate(item)
        equipment_data.lab_name = item.lab.name if item.lab else None
        result_list.append(equipment_data)

    return PageResponse(list=result_list, total=total)


async def create_equipment(data: EquipmentCreateRequest, db: AsyncSession):
    result = await db.execute(select(Lab).where(Lab.id == data.lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise BusinessException(message="实验室不存在，新增失败")

    result = await db.execute(
        select(Equipment).where(
            and_(Equipment.lab_id == data.lab_id, Equipment.name == data.name)
        )
    )
    duplicated = result.scalar_one_or_none()
    if duplicated:
        raise BusinessException(message="实验室已经存在此种设备")

    new_equipment = Equipment(**data.model_dump())

    db.add(new_equipment)
    await db.commit()
    await db.refresh(new_equipment)

    equipment_data = EquipmentResponse.model_validate(new_equipment)
    # 直接复用上面已加载的实验室对象，避免在异步会话里惰性加载 new_equipment.lab
    equipment_data.lab_name = lab.name

    return equipment_data


async def update_equipment(
    equipment_id: int, data: EquipmentUpdateRequest, db: AsyncSession
):
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise BusinessException(message="设备不存在")

    data_dict = data.model_dump(exclude_none=True)
    lab_id = data_dict.get("lab_id", equipment.lab_id)
    name = data_dict.get("name", equipment.name)

    result = await db.execute(select(Lab).where(Lab.id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise BusinessException(message="实验室不存在，更新失败")

    result = await db.execute(
        select(Equipment).where(
            and_(
                Equipment.lab_id == lab_id,
                Equipment.name == name,
                Equipment.id != equipment.id,
            )
        )
    )
    duplicated = result.scalar_one_or_none()
    if duplicated:
        raise BusinessException(message="实验室已存在此种设备，更新失败")

    for field, value in data_dict.items():
        setattr(equipment, field, value)

    await db.commit()
    await db.refresh(equipment)

    equipment_data = EquipmentResponse.model_validate(equipment)
    equipment_data.lab_name = lab.name

    return equipment_data


async def delete_equipment(equipment_id: int, db: AsyncSession):
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise BusinessException(message="设备不存在")

    await db.delete(equipment)
    await db.commit()
