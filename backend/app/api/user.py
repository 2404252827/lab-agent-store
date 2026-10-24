from fastapi import APIRouter, Depends, Query
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_admin, get_current_user
from app.models.user import User
from app.schemas.user import PasswordUpdateRequest, UserCreateRequest, UserUpdateRequest
from app.services import user_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return Response.success(data=user_service.get_user_info(current_user))


@router.put("/update")
async def update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户更新自身信息"""
    res = await user_service.update_user_info(data, current_user, db)
    return Response.success(message="用户信息更新成功", data=res)


@router.put("/password")
async def update_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户密码"""
    await user_service.update_password(data, current_user, db)
    return Response.success(message="密码修改成功")


@router.get("/list")
async def get_user_page_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, max_length=50),
):
    """获取用户列表

    分页查询非管理员用户，`keyword` 同时模糊匹配 `username` 和 `nickname`。
    """
    res = await user_service.get_user_page_list(db, page, page_size, keyword)
    return Response.success(data=res)


@router.post("")
async def create_user(
    data: UserCreateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员新增用户"""
    res = await user_service.create_user(data=data, db=db)
    return Response.success(message="新增用户成功", data=res)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    user: User = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新用户信息"""
    res = await user_service.update_user(user_id=user_id, data=data, db=db)
    return Response.success(message="更新用户成功", data=res)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, user: User = Depends(get_admin), db: AsyncSession = Depends(get_db)
):
    """管理员删除用户"""
    await user_service.delete_user(user_id, user, db)
    return Response.success(message="删除用户成功")

