import asyncio
import json
import logging

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from pydantic import SecretStr

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.user import User
from app.pg_database import PgSessionFactory
from app.schemas.ai import ChatRequest, ChatResponse
from app.services import chat_history_service
from app.services.agent_tools import build_tools

_model: ChatOpenAI | None = None

logger = logging.getLogger(__name__)

# 送给模型的历史条数由 settings.CHAT_CONTEXT_LIMIT 控制

# 一轮对话里最多允许「思考 → 调工具」几轮。不限制的话，模型可能反复调同一个工具，把额度和时间烧光
RECURSION_LIMIT = 25

SYSTEM_PROMPT = """你是「智能实验室」管理系统的 AI 助手，服务对象是学校的老师和学生。

## 你的职责范围
你只负责三件事：
1. 帮用户查询实验室和实验设备的信息；
2. 帮用户提交实验室预约申请，以及查询用户自己的预约记录；
3. 解答实验室的规章制度、预约规则、操作流程问题。

跟实验室管理系统无关的问题（天气、闲聊、写代码、通用知识问答等），
礼貌说明你只负责实验室相关事务，然后请用户换一个问题，不要强行回答。

## 工具使用策略
- 凡是涉及具体数据（有哪些实验室、设备型号、预约记录、某天能否预约），
  必须先调用工具查证，绝对不要凭印象回答。
- 涉及规则、制度、流程、「为什么」「能不能」这类问题，用 search_lab_rules 检索知识库。
- 涉及具体数据的问题不要用 search_lab_rules，它查的是文档不是数据库。
- 需要知道今天是几号（用户说「明天」「下周三」等）时，**先调用 get_current_date**，
  不要凭记忆猜日期。
- 可以一次调用多个工具，也可以根据上一步结果接着调下一个。

## 预约的硬性要求
- 调用 create_lab_reservation 前，必须已经从用户那里拿到四项明确信息：
  实验室名称、日期、开始时间、结束时间。缺哪一项就先问清楚，不要自己填。
- 日期必须先通过 get_current_date 拿到今天，再换算成 YYYY-MM-DD 的绝对日期。
- 时间必须是 HH:MM。用户说「下午两点」要换算成 14:00。
- 工具返回失败原因（比如「请提前一天进行预约」）时，如实转述并给出建议。

## 回答要求
- 中文回答，简洁准确，不要啰嗦。
- 不要提到「工具」「知识库」「资料1」「检索」这类字眼，
  就当这些信息是你本来就掌握的。
- 列表信息用简洁的列表或表格呈现，不要大段堆砌。
- 工具没查到结果时如实说查不到，不要编造。"""


def get_model() -> ChatOpenAI:
    global _model

    if _model is None:
        if not settings.DEEPSEEK_API_KEY:
            raise BusinessException(message="未配置 DEEPSEEK_API_KEY，请在 .env 中补上")

        _model = ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=SecretStr(settings.DEEPSEEK_API_KEY),
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=60,
            max_retries=2,
        )

    return _model


def build_graph(model: ChatOpenAI, tools, system_prompt: str):

    model_with_tools = model.bind_tools(tools)

    async def call_model_node(state: MessagesState):
        response = await model_with_tools.ainvoke(
            [SystemMessage(content=system_prompt), *state["messages"]]
        )

        return {"messages": [response]}

    builder = StateGraph(MessagesState)

    builder.add_node("agent", call_model_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()


def _to_business_error(exc: Exception) -> BusinessException:

    if isinstance(exc, AuthenticationError):
        return BusinessException(message="大模型鉴权失败，请检查 DEEPSEEK_API_KEY")

    if isinstance(exc, APITimeoutError):
        return BusinessException(message="大模型响应超时，请稍后重试")

    if isinstance(exc, RateLimitError):
        return BusinessException(message="大模型调用频率超限，请稍后重试")

    if isinstance(exc, APIStatusError):
        return BusinessException(message=f"大模型服务异常（HTTP {exc.status_code}）")

    if isinstance(exc, APIConnectionError):
        return BusinessException(message="无法连接大模型服务，请检查网络或 BASE_URL")

    return BusinessException(message="AI 服务暂时不可用")


async def _load_context(user_id: int, question: str) -> list:
    """读取该用户最近的历史，并在末尾追加本次问题。

    CHAT_CONTEXT_LIMIT 是「送给模型的总条数」，所以历史取 limit - 1 条，
    再加上本次问题正好 limit 条。

    注意：会话只在这几行里短暂持有，大模型调用期间不占数据库连接。
    """

    limit = max(1, settings.CHAT_CONTEXT_LIMIT)

    async with PgSessionFactory() as db:
        records = await chat_history_service.list_messages(db, user_id, limit - 1)

    messages = [
        HumanMessage(content=record.content)
        if record.role == "user"
        else AIMessage(content=record.content)
        for record in records
    ]
    messages.append(HumanMessage(content=question))

    return messages


async def _save_exchange(user_id: int, question: str, answer: str) -> None:
    """保存一问一答。

    持久化失败不应该让用户拿不到已经生成的回答，
    所以这里只记日志，不向上抛异常。
    """

    try:
        async with PgSessionFactory() as db:
            await chat_history_service.append_exchange(db, user_id, question, answer)
    except Exception:
        logger.exception("保存 AI 对话历史失败 user_id=%s", user_id)


# ai建议
def _text_of(message) -> str:
    """把一条消息的正文取成纯文本

    正常情况下 content 是字符串，但有些模型会返回
    [{"type": "text", "text": "..."}] 这种结构，这里统一处理掉。
    """

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts).strip()

    return ""


def _extract_answer(messages) -> str:

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = _text_of(message)
            if text:
                return text

    return "模型这次没有给出回答，请重新发送一次。"


async def chat(data: ChatRequest, user: User) -> ChatResponse:
    """非流式对话：读历史 → 跑 agent → 成功后成对写入"""

    try:
        messages = await _load_context(user.id, data.content)
    except Exception as exc:
        logger.exception("读取对话历史失败 user_id=%s", user.id)
        raise BusinessException(message="读取对话历史失败，请稍后重试") from exc

    tools = build_tools(user)
    graph = build_graph(get_model(), tools, SYSTEM_PROMPT)

    try:
        result = await graph.ainvoke(
            {"messages": messages}, config={"recursion_limit": RECURSION_LIMIT}
        )
    except Exception as exc:
        logger.exception("Agent 执行失败 user_id=%s", user.id)
        raise _to_business_error(exc) from exc

    answer = _extract_answer(result["messages"])

    # 只有成功拿到回答才写入，避免「只存了问题没存回答」的半截会话
    await _save_exchange(user.id, data.content, answer)

    # 把模型实际调了哪些工具记下来。agent 出错时，方便查看
    used = [
        f"{call['name']}({call.get('args')})"
        for message in result["messages"]
        for call in (getattr(message, "tool_calls", None) or [])
    ]

    logger.info(
        "Agent 对话完成 user_id=%s 消息数=%d 调用工具=%s",
        user.id,
        len(result["messages"]),
        used or "无",
    )

    return ChatResponse(content=answer)


async def stream_chat(data: ChatRequest, user: User):
    """流式对话：读历史 → 流式跑 agent → 成功后成对写入

    只有完整跑完才会把一问一答写进 PostgreSQL。
    客户端中断或模型报错时都不写入，避免留下半截会话。
    """

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    try:
        messages = await _load_context(user.id, data.content)
        tools = build_tools(user)
        graph = build_graph(get_model(), tools, SYSTEM_PROMPT)
    except BusinessException as exc:
        yield sse({"type": "error", "message": exc.message})
        return
    except Exception:
        logger.exception("流式对话初始化失败 user_id=%s", user.id)
        yield sse({"type": "error", "message": "AI 服务暂时不可用"})
        return

    seen_tools: set[str] = set()
    parts: list[str] = []

    try:
        async for chunk, _metadata in graph.astream(
            {"messages": messages},
            config={"recursion_limit": RECURSION_LIMIT},
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue

            for call in getattr(chunk, "tool_call_chunks", None) or []:
                name = call.get("name")
                if name and name not in seen_tools:
                    seen_tools.add(name)
                    yield sse({"type": "tool", "name": name})

            # content 是增量片段，直接往前端丢
            text = _text_of(chunk)
            if text:
                parts.append(text)
                yield sse({"type": "token", "content": text})

        answer = "".join(parts).strip()

        if not answer:
            # 模型只思考没输出时，也要给前端一句兜底，否则气泡会是空的
            answer = "模型这次没有给出回答，请重新发送一次。"
            yield sse({"type": "token", "content": answer})

        await _save_exchange(user.id, data.content, answer)

        yield sse({"type": "done"})
        logger.info(
            "流式对话完成 user_id=%s 工具=%s 回答长度=%d",
            user.id,
            sorted(seen_tools) or "无",
            len(answer),
        )

    except asyncio.CancelledError:
        # 前端主动断开连接，属于正常情况，不要记成错误，也不落库
        logger.info("客户端断开，流式对话中止 user_id=%s", user.id)
        raise

    except Exception as exc:
        logger.exception("流式对话失败 user_id=%s", user.id)
        yield sse({"type": "error", "message": _to_business_error(exc).message})
