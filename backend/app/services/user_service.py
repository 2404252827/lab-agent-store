from sqlalchemy import func, or_, select

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import password
from app.utils.password import hash_password, verify_password


def get_user_info(user: User):
    return UserResponse.model_validate(user)


async def update_user_info(data: UserUpdateRequest, user: User, db: AsyncSession):
    data_dict = data.model_dump(exclude_none=True)
    for filed, value in data_dict.items():
        setattr(user, filed, value)

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


async def update_password(data: PasswordUpdateRequest, user: User, db: AsyncSession):
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误")

    user.password = hash_password(data.new_password)

    await db.commit()
    await db.refresh(user)


async def get_user_page_list(
    db: AsyncSession, page: int, page_size: int, keyword: str | None = None
):
    stmt = select(User).where(User.role != "admin")
    count_stmt = select(func.count(User.id)).where(User.role != "admin")

    if keyword:
        stmt = stmt.where(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%"),
            )
        )
        count_stmt = count_stmt.where(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%"),
            )
        )

    stmt = stmt.order_by(User.id.desc())
    stmt = stmt.offset(offset=(page - 1) * page_size).limit(page_size)

    result_page = await db.execute(stmt)
    items = result_page.scalars().all()
    total = await db.scalar(count_stmt)

    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items], total=total
    )


async def create_user(data: UserCreateRequest, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == data.username))
    exist = result.scalar_one_or_none()

    if exist:
        raise BusinessException(message="创建用户失败，该账号已存在")

    new_user = User(
        username=data.username,
        password=hash_password(data.password),
        nickname=data.nickname,
        email=data.email,
        phone=data.phone,
        role=data.role,
        avatar=data.avatar,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


async def update_user(user_id: int, data: UserUpdateRequest, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise BusinessException(message="更新用户失败，用户不存在")

    data_dict = data.model_dump(exclude_none=True)
    for filed, value in data_dict.items():
        setattr(user, filed, value)

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


async def delete_user(user_id: int, current_user: User, db: AsyncSession):
    if user_id == current_user.id:
        raise BusinessException(message="删除用户失败，不能删除当前登录用户")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise BusinessException(message="删除用户失败，用户不存在")

    await db.delete(user)
    await db.commit()
