import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import UPLOAD_DIR
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import Base, async_engine
from starlette.middleware.cors import CORSMiddleware
from app.common.middlewares import ServerErrorCatchMiddleware
from app.services import reservation_service
from app.models.chat import ChatMessageRecord  # noqa: F401  让 PgBase 注册这张表
from app.pg_database import PgBase, pg_engine


# 使用异步引擎创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("数据库表检查/创建完成")

    # 对话历史在独立的 PostgreSQL 里，Base 和 PgBase 必须分开建表
    async with pg_engine.begin() as conn:
        await conn.run_sync(PgBase.metadata.create_all)
        print("对话历史表检查/创建完成")

    cancel_scan_task = asyncio.create_task(
        reservation_service.run_cancel_scan(), name="cancel_scan"
    )
    yield
    # .cancel()只是发出取消信号，等到真正退出再去进行异步引擎的关闭
    try:
        cancel_scan_task.cancel()
    except asyncio.CancelledError:
        pass
    await pg_engine.dispose()
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan)

# 设置浏览器跨域
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# 中间件注册顺序很关键，别调换：Starlette 中「后注册的中间件更靠外层」，
# 而跨域头是由最外层的 CORSMiddleware 补上的。
# 所以这里先注册兜底异常中间件（位于 CORS 内层），再注册 CORSMiddleware（外层），
# 这样未捕获异常返回的 500 响应才会带上 Access-Control-Allow-Origin。
# 顺序写反的话，500 没有跨域头 → 被浏览器直接拦截 → 前端只能看到「网络异常」。
# 详见 app/common/middlewares.py 里的说明。
# 该中间件由ai生成
app.add_middleware(ServerErrorCatchMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api import api

app.include_router(api)

# 注册异常处理器
from app.common.exceptions import register_exception_handlers

register_exception_handlers(app)

# 挂载静态的文件目录
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
