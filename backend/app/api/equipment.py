from fastapi import APIRouter, Depends, Query
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_admin, get_current_user
from app.models.user import User
from app.schemas.equipment import EquipmentCreateRequest, EquipmentUpdateRequest
from app.services import equipment_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/equipment", tags=["设备信息接口"])


@router.get("/list")
async def get_equipment_page_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, max_length=50),
    lab_id: int | None = None,
):
    """获取设备列表"""
    res = await equipment_service.get_equipment_page_list(
        db, page, page_size, keyword, lab_id
    )
    return Response.success(data=res)


@router.post("")
async def create_equipment(
    data: EquipmentCreateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员新增设备"""
    res = await equipment_service.create_equipment(data=data, db=db)
    return Response.success(message="新增设备成功", data=res)


@router.put("/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新设备信息"""
    res = await equipment_service.update_equipment(
        equipment_id=equipment_id, data=data, db=db
    )
    return Response.success(message="更新设备信息成功", data=res)


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除设备"""
    await equipment_service.delete_equipment(equipment_id, db)
    return Response.success(message="删除设备成功")
