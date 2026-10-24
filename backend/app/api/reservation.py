from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_admin, get_current_user
from app.models.user import User
from app.schemas.reservation import AuditReservationRequest, ReservationCreateRequest
from app.services import reservation_service

router = APIRouter(prefix="/reservation", tags=["预约接口信息"])


@router.post("")
async def create_reservation(
    data: ReservationCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户预约实验室"""
    res = await reservation_service.create_reservation(data, user, db)
    return Response.success(message="预约成功", data=res)


@router.get("/list")
async def get_reservation_page_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int | None = Query(None, ge=0, le=3),
    lab_id: int | None = Query(None, ge=1),
):
    """管理员获取预约管理，用户获得我的预约"""
    res = await reservation_service.get_reservation_page_list(
        db, user, page, page_size, status, lab_id
    )
    return Response.success(message="获取列表成功", data=res)


@router.get("/dates")
async def get_reserved_lab_date(
    lab_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取实验室已被预约的日期（供前端日期选择器标红）"""
    res = await reservation_service.get_reserved_lab_date(lab_id, db)
    return Response.success(data=res)


@router.put("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户取消预约"""
    await reservation_service.cancel_reservation(reservation_id, user, db)
    return Response.success(message="取消预约成功")


@router.put("/{reservation_id}/audit")
async def audit_reservation(
    reservation_id: int,
    data: AuditReservationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_admin),
):
    """管理员审核预约"""
    await reservation_service.audit_reservation(reservation_id, data, db)
    return Response.success(message="审核成功")
