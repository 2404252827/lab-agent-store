"""自定义中间件。

这里只有一个「兜底异常中间件」，用来解决一个很容易踩的坑：

未捕获异常产生的 500 响应，默认是由 Starlette 的 ServerErrorMiddleware 生成的，
而 ServerErrorMiddleware 位于 CORSMiddleware 的 **外层**，所以这个 500 响应
不会经过跨域处理、不带 Access-Control-Allow-Origin 头。浏览器会因此直接拦截响应，
前端 axios 拿不到任何 response，只能提示「网络异常」——真正的 500 错误就被掩盖了。

所以这里在 CORSMiddleware 的 **内层** 再兜一层：捕获未被处理的异常，
返回项目统一的 JSON 信封，这个响应随后会被外层的 CORSMiddleware 补上跨域头。

注册顺序见 app/main.py：本中间件必须 **先于** CORSMiddleware 注册。
（Starlette 中「后注册的中间件更靠外层」，先注册的才在 CORS 内层。）
"""

# agent生成
import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common.response import Response

logger = logging.getLogger(__name__)


class ServerErrorCatchMiddleware:
    """捕获未处理异常，返回统一信封（500），并保证外层 CORS 能补上跨域头。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # 非 HTTP 请求（lifespan / websocket）直接透传
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message) -> None:
            # 记录响应是否已经开始发送：已经开始就不能再写第二个响应了
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # 打印完整堆栈，方便在控制台直接定位后端问题
            logger.exception(
                "未处理的异常：%s %s", scope.get("method"), scope.get("path")
            )

            # 例如静态文件流式下载已开始发送响应，此时无法替换，继续向上抛由外层处理
            if response_started:
                raise

            response = JSONResponse(
                status_code=500,
                content=Response.error(code=500, message="服务器内部错误").model_dump(),
            )
            await response(scope, receive, send)
