from fastapi.concurrency import run_in_threadpool
from sqlalchemy import RollbackToSavepointClause, select
from app.common.exceptions import BusinessException
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.utils import password
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token


async def login(data: LoginRequest, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    # bcrypt中的verify_password是同步函数
    # 会造成每当有一个用户在登陆时，系统就会有一个验证密码的延迟，在此期间系统不能做其他请求
    if not user or not await run_in_threadpool(
        verify_password, data.password, user.password
    ):
        raise BusinessException(message="账号或密码错误")

    if user.status != 1:
        raise BusinessException(message="用户已被禁用", code=403)

    token = create_access_token(user.id)

    return LoginResponse(token=token, user=UserResponse.model_validate(user))


async def register(data: RegisterRequest, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if user:
        raise BusinessException(message="用户已存在")

    if data.role == "admin":
        raise BusinessException(message="不能注册为管理员")

    # 和login中同理
    password = await run_in_threadpool(hash_password, data.password)
    new_user = User(
        username=data.username,
        password=password,
        nickname=data.nickname or data.username,
        role=data.role,
        phone=data.phone,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
