from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.response import Response


class BusinessException(Exception):
    """自定义业务逻辑异常"""

    def __init__(self, message: str, code: int = 500) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """自定义业务逻辑异常处理器"""
        return JSONResponse(
            status_code=200,
            content=Response.error(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器"""
        return JSONResponse(
            status_code=exc.status_code,
            content=Response.error(
                code=exc.status_code, message=str(exc.detail)
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """请求参数异常处理器"""
        errors = exc.errors()

        if errors:
            first = errors[0]
            field = ".".join(
                str(item) for item in first.get("loc", ()) if item != "body"
            )
            detail = str(first.get("msg", "")).replace("Value error, ", "")
            message = f"参数校验失败：{field} {detail}".strip()
        else:
            message = "请求参数校验错误"

        return JSONResponse(
            status_code=422,
            content=Response.error(code=422, message=message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器（最后一道保险）

        注意：这个处理器由 Starlette 的 ServerErrorMiddleware 调用，而它位于
        CORSMiddleware 外层，所以这里返回的 500 不带跨域头、会被浏览器拦截。
        正常情况下未捕获异常会先被内层的 ServerErrorCatchMiddleware 处理并返回
        带跨域头的 500（见 app/common/middlewares.py），这里只作为兜底。
        """
        return JSONResponse(
            status_code=500,
            content=Response.error(code=500, message="服务器内部错误").model_dump(),
        )

