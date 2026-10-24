import asyncio
from datetime import date, datetime

from sqlalchemy import and_, func, select

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.database import AsyncSessionFactory
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import (
    AuditReservationRequest,
    ReservationCreateRequest,
    ReservationResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import logging
from sqlalchemy import and_, func, or_, select

logger = logging.getLogger(__name__)

# 生效中的预约状态：待审核、已同意
ACTIVE_STATUS = (0, 1)
CANCEL_SCAN_INTERVAL = 60


async def create_reservation(
    data: ReservationCreateRequest, user: User, db: AsyncSession
):
    """预约实验室"""

    # 使用with_for_update()进行加排他锁，直到事务提交才会释放
    # 避免多用户同时进行实验预约，同时成功的情况
    result = await db.execute(
        select(Lab).where(Lab.id == data.lab_id).with_for_update()
    )
    lab = result.scalar_one_or_none()

    if not lab:
        raise BusinessException(message="实验室不存在，预约失败")

    if lab.status != 1:
        raise BusinessException(message="实验室已关闭，暂不可预约")

    today = datetime.now().date()

    try:
        reservation_date = date.fromisoformat(data.date)
    except ValueError:
        raise BusinessException(message="预约日期无效")

    if (reservation_date - today).days < 1:
        raise BusinessException(message="请提前一天进行预约")

    if data.start_time >= data.end_time:
        raise BusinessException(message="结束时间需要晚于开始时间")

    open_time = lab.open_time or ""
    close_time = lab.close_time or ""

    if open_time and close_time:
        if data.start_time < open_time or data.end_time > close_time:
            raise BusinessException(
                message=f"预约时间需在实验室开放时间内（{open_time} - {close_time}）"
            )

    # 同一用户同一天对同一实验室只允许一条生效中的预约
    result = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.user_id == user.id,
                Reservation.lab_id == data.lab_id,
                Reservation.date == data.date,
                Reservation.status.in_(ACTIVE_STATUS),
            )
        )
    )

    if result.scalars().all():
        raise BusinessException(message="您当天已预约该实验室，请勿重复预约")

    # 同一时间段只能有一条生效中的预约（区间重叠判断）
    result = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.lab_id == data.lab_id,
                Reservation.date == data.date,
                Reservation.status.in_(ACTIVE_STATUS),
                Reservation.start_time < data.end_time,
                Reservation.end_time > data.start_time,
            )
        )
    )

    if result.scalars().all():
        raise BusinessException(message="该时间段已经被预约了")

    new_reservation = Reservation(
        user_id=user.id,
        lab_id=data.lab_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        remark=data.remark,
        status=0,
    )

    db.add(new_reservation)
    await db.commit()
    await db.refresh(new_reservation)

    return ReservationResponse.model_validate(new_reservation)


async def get_reserved_lab_date(lab_id: int, db: AsyncSession):
    """获取实验室被预约的日期，优化前端用户体验（日期选择器标红）

    只返回「今天及以后、且处于生效状态」的预约日期，去重后按日期升序排列。
    """

    today = datetime.now().strftime("%Y-%m-%d")

    result = await db.execute(
        select(Reservation.date)
        .where(
            and_(
                Reservation.lab_id == lab_id,
                Reservation.status.in_(ACTIVE_STATUS),
                Reservation.date >= today,
            )
        )
        .distinct()
        .order_by(Reservation.date)
    )

    return list(result.scalars().all())


async def get_reservation_page_list(
    db: AsyncSession,
    user: User,
    page: int,
    page_size: int,
    status: int | None = None,
    lab_id: int | None = None,
):
    """获得预约列表，用户获得我的预约，管理员获得全部预约"""

    # 进行预加载
    stmt = select(Reservation).options(
        selectinload(Reservation.lab), selectinload(Reservation.user)
    )
    stmt_count = select(func.count(Reservation.id))

    if user.role != "admin":
        stmt = stmt.where(Reservation.user_id == user.id)
        stmt_count = stmt_count.where(Reservation.user_id == user.id)

    if status is not None:
        stmt = stmt.where(Reservation.status == status)
        stmt_count = stmt_count.where(Reservation.status == status)

    if lab_id is not None:
        stmt = stmt.where(Reservation.lab_id == lab_id)
        stmt_count = stmt_count.where(Reservation.lab_id == lab_id)

    stmt = stmt.order_by(Reservation.id.desc())
    stmt = stmt.offset(offset=(page - 1) * page_size).limit(page_size)

    result_page = await db.execute(stmt)
    items = result_page.scalars().all()
    total = await db.scalar(stmt_count)

    result_list = []
    for item in items:
        reservation_data = ReservationResponse.model_validate(item)
        reservation_data.username = item.user.username if item.user else None
        reservation_data.nickname = item.user.nickname if item.user else None
        reservation_data.lab_name = item.lab.name if item.lab else None
        result_list.append(reservation_data)

    return PageResponse(list=result_list, total=total)


async def cancel_reservation(reservation_id: int, user: User, db: AsyncSession):
    """用户取消预约"""

    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise BusinessException(message="该预约不存在")

    if reservation.user_id != user.id:
        raise BusinessException(message="无权限", code=403)

    if reservation.status != 0:
        raise BusinessException(message="当前状态不能取消")

    reservation.status = 3
    await db.commit()


async def audit_reservation(
    reservation_id: int, data: AuditReservationRequest, db: AsyncSession
):
    """管理员审核预约"""

    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise BusinessException(message="该预约不存在")

    if data.status not in [1, 2]:
        raise BusinessException(message="审核状态错误")

    if reservation.status != 0:
        raise BusinessException(message="该状态不支持审核")

    reservation.status = data.status
    await db.commit()


async def _auto_cancel_expired_reservation() -> int:
    """把「时间已过但还挂在待审核」的预约自动置为已取消"""

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    async with AsyncSessionFactory() as db:
        result = await db.execute(
            select(Reservation).where(
                Reservation.status == 0,
                or_(
                    Reservation.date < today,
                    and_(
                        Reservation.date == today,
                        Reservation.end_time < current_time,
                    ),
                ),
            )
        )
        expired = result.scalars().all()

        if not expired:
            return 0

        for reservation in expired:
            reservation.status = 3

        await db.commit()

        return len(expired)


async def run_cancel_scan() -> None:
    """后台循环：定期清理过期未处理的预约"""

    while True:
        try:
            count = await _auto_cancel_expired_reservation()

            if count:
                logger.info("自动取消过期预约 %d 条", count)
        except Exception:
            # 循环体必须兜住异常：否则一次数据库抖动就让这个 while 退出，后台任务静默死掉，之后再也不扫描，而且不会留下任何报错。
            # ai建议的
            logger.exception("自动取消过期预约失败，%d 秒后重试", CANCEL_SCAN_INTERVAL)

        await asyncio.sleep(CANCEL_SCAN_INTERVAL)
