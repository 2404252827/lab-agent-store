from fastapi import APIRouter, Depends, Query
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_admin, get_current_user
from app.models.user import User
from app.schemas.lab import LabCreateRequest, LabUpdateRequest
from app.services import lab_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/lab", tags=["实验室信息接口"])


@router.get("/list")
async def get_lab_page_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, max_length=50),
):
    """获取实验室列表

    所有登录用户都可以查看实验室信息，`keyword` 模糊匹配实验室名称。
    """
    res = await lab_service.get_lab_page_list(db, page, page_size, keyword)
    return Response.success(data=res)


@router.post("")
async def create_lab(
    data: LabCreateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员新增实验室"""
    res = await lab_service.create_lab(data=data, db=db)
    return Response.success(message="新增实验室成功", data=res)


@router.put("/{lab_id}")
async def update_lab(
    lab_id: int,
    data: LabUpdateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新实验室信息"""
    res = await lab_service.update_lab(lab_id=lab_id, data=data, db=db)
    return Response.success(message="更新实验室成功", data=res)


@router.delete("/{lab_id}")
async def delete_lab(
    lab_id: int, user: User = Depends(get_admin), db: AsyncSession = Depends(get_db)
):
    """管理员删除实验室"""
    await lab_service.delete_lab(lab_id, db)
    return Response.success(message="删除实验室成功")
