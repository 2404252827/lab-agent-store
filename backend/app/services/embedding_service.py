from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.common.exceptions import BusinessException
from app.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client

    if _client is None:
        if not settings.SILICONFLOW_API_KEY:
            raise BusinessException(message="嵌入模型没有配置api_key")
        _client = AsyncOpenAI(
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_BASE_URL,
            timeout=60,
            max_retries=2,
        )

    return _client


def _to_business_error(exc: Exception) -> BusinessException:
    """把 SDK 异常翻译成中文提示，和 ai_service 里的思路一致"""

    if isinstance(exc, AuthenticationError):
        return BusinessException(message="嵌入模型鉴权失败，请检查 SILICONFLOW_API_KEY")

    if isinstance(exc, APITimeoutError):
        return BusinessException(message="嵌入模型响应超时，请稍后重试")

    if isinstance(exc, RateLimitError):
        return BusinessException(message="嵌入模型调用频率超限，请稍后重试")

    if isinstance(exc, APIStatusError):
        return BusinessException(message=f"嵌入模型服务异常（HTTP {exc.status_code}）")

    if isinstance(exc, APIConnectionError):
        return BusinessException(message="无法连接嵌入模型服务，请检查网络")

    return BusinessException(message="向量化服务暂时不可用")


async def _embed_batch(texts: list[str]) -> list[list[float]]:
    client = get_client()

    try:
        result = await client.embeddings.create(
            model=settings.SILICONFLOW_EMBED_MODEL,
            input=texts,
            encoding_format="float",
        )
    except Exception as exc:
        raise _to_business_error(exc) from exc

    # 接口不保证返回顺序和请求顺序一致，按 index 排好再取，否则向量会和文本错位
    ordered = sorted(result.data, key=lambda item: item.index)
    vectors = [list(item.embedding) for item in ordered]

    if len(vectors) != len(texts):
        raise BusinessException(message="嵌入模型返回的向量数量与请求不一致")

    if len(vectors[0]) != settings.EMBED_DIM:
        raise BusinessException(message="模型返回的维度和配置不一致")

    return vectors


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    batch_size = settings.EMBED_BATCH_SIZE
    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(await _embed_batch(batch))

    return vectors


async def embed_query(text: str) -> list[float]:

    vectors = await embed_texts([text])

    return vectors[0]
