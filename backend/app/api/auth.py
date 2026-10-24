from fastapi import APIRouter, Depends
from app.common.response import Response
from app.schemas.auth import LoginRequest, RegisterRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录接口"""
    result = await auth_service.login(data, db)
    return Response.success(data=result)


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册接口"""
    await auth_service.register(data, db)
    return Response.success(message="用户注册成功")
