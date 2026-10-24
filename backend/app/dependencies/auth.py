from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import BusinessException
from app.database import get_db
from app.utils.jwt import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    description=(
        "先调用 `POST /api/auth/login` 获取 token（在响应体的 `data.token` 里），"
        "再把它原样粘贴到这里，Swagger UI 会自动补上 `Bearer ` 前缀。"
    ),
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效，请重新登录",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录"
        )

    user_id = payload.get("user_id", {})

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录凭证"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户被禁用"
        )

    return user


async def get_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise BusinessException(message="需要管理员权限")
    return user
