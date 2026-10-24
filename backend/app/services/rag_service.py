from os import name
from typing import Any

import logging

from pymilvus import DataType, MilvusClient
from starlette.concurrency import run_in_threadpool

from app.common.exceptions import BusinessException
from app.config import CHROMA_DIR, KB_DIR, settings
from app.services import embedding_service

logger = logging.getLogger(__name__)

_client: Any | None = None
_ready = False

_ID_MAX = 512
_SOURCE_MAX = 512
_HEADING_MAX = 1024
_DOCUMENT_MAX = 8192
_INSERT_BATCH = 500


def get_client() -> MilvusClient:
    global _client

    if _client is None:
        _client = MilvusClient(
            uri=settings.MILVUS_URI,
            token=settings.MILVUS_TOKEN or "",
            db_name=settings.MILVUS_DB_NAME or "",
            timeout=10,
        )

    return _client


def _build_schema(client: MilvusClient):

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)

    # 主键用 VARCHAR 而不是自增 INT：chunk 的 id 是 "kb/xx.md#0" 这种稳定字符串，
    # 重复入库时同一个 id 会覆盖，不会产生重复片段
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=_ID_MAX)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=settings.EMBED_DIM)
    schema.add_field("document", DataType.VARCHAR, max_length=_DOCUMENT_MAX)
    schema.add_field("source", DataType.VARCHAR, max_length=_SOURCE_MAX)
    schema.add_field("heading", DataType.VARCHAR, max_length=_HEADING_MAX)
    schema.add_field("chunk", DataType.INT64)

    return schema


def ensure_collection():

    global _ready

    if _ready:
        return

    client = get_client()
    name = settings.MILVUS_COLLECTION
    created = False

    if not client.has_collection(name):
        index_params = client.prepare_index_params()

        # 向量索引：HNSW + COSINE
        # bge-m3 的向量是归一化的，用 COSINE 最合适。
        # M / efConstruction 是 HNSW 的建图参数，M=16 是通用默认值
        index_params.add_index(
            field_name="vector",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )

        # source 建倒排索引：重新入库前要按 source 删除旧数据，
        # 没有索引这个 delete 会退化成全表扫描
        index_params.add_index(field_name="source", index_type="INVERTED")

        client.create_collection(
            collection_name=name,
            schema=_build_schema(client),
            index_params=index_params,
        )
        created = True
        logger.info("Milvus 集合已创建：%s", name)

    if not created:
        # 已存在的集合：Milvus 重启后加载状态会丢，这里补一次 load。
        # 已经 load 过时会抛异常，忽略即可
        try:
            client.load_collection(name)
        except Exception as exc:
            logger.debug("load_collection 跳过：%s", exc)

    _ready = True


# ai建议
def _count_rows() -> int:
    """准确行数

    不要用 get_collection_stats()["row_count"]：它对 delete 是最终一致的，
    实测删掉 2 条后仍然返回删除前的数量。
    """

    client = get_client()
    result = client.query(
        settings.MILVUS_COLLECTION,
        filter="",
        output_fields=["count(*)"],
    )

    if not result:
        return 0

    return int(result[0].get("count(*)") or 0)


# -----------------------------分块----------------------------------
# 不使用langchain已经封装好的分块
def _split_markdown(
    text: str, max_chars: int, overlap: int = 100
) -> list[tuple[str, str]]:
    """
    把一篇 markdown 切成若干块，返回 [(标题路径, 正文), ...]

    策略：先按标题切成「小节」，小节还太长就按段落继续切。

    每块都带上它所属的标题路径，这样检索出来的片段能自己说明「我是哪一节的」，
    模型判断相关性会准很多。标题也会一起被向量化，等于多了一份语义信息。
    """
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    heading_stack: list[str] = []
    current: list[str] = []
    current_path = ""

    def flush() -> None:
        body = "\n".join(current).strip()
        if body:
            sections.append((current_path, list(current)))

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()

            flush()
            current.clear()

            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            current_path = ">".join(heading_stack)
        else:
            current.append(line)

    flush()

    chunks: list[tuple[str, str]] = []

    for path, body_lines in sections:
        paragraphs = [p.strip() for p in "\n".join(body_lines).split("\n\n")]
        paragraphs = [p for p in paragraphs if p]

        buffer = ""

        for para in paragraphs:
            if len(para) > max_chars:
                if buffer:
                    chunks.append((path, buffer))
                    buffer = ""
                for start in range(0, len(para), max_chars):
                    chunks.append((path, para[start : start + max_chars]))

                continue

            if buffer and len(buffer) + len(para) + 2 > max_chars:
                chunks.append((path, buffer))
                buffer = (buffer[-overlap:] + "\n\n" + para).strip()
            else:
                buffer = (buffer + "\n\n" + para).strip() if buffer else para

        if buffer:
            chunks.append((path, buffer))

    return chunks


def load_chunks():
    if not KB_DIR.exists():
        raise BusinessException(message="知识库目录不存在")

    files = sorted(KB_DIR.rglob("*.md"))

    if not files:
        raise BusinessException(message="知识数据库没有md文件")

    chunks: list[dict] = []

    for path in files:
        source = path.relative_to(KB_DIR.parent).as_posix()
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        for index, (heading, body) in enumerate(
            _split_markdown(text, settings.RAG_MAX_CHUNK_CHARS)
        ):
            chunks.append(
                {
                    # id 必须唯一且稳定：同一份文件重复入库时会覆盖旧数据，不会出现越跑越多份的重复片段
                    "id": f"{source}#{index}",
                    "document": f"【{heading}】\n{body}" if heading else body,
                    "metadata": {
                        "source": source,
                        "heading": heading,
                        "chunk": index,
                        "length": len(body),
                    },
                }
            )

    return chunks


# ---------------------------------------入库--------------------------------
def _reset_collection() -> None:
    global _ready

    client = get_client()
    name = settings.MILVUS_COLLECTION

    if client.has_collection(name):
        client.drop_collection(name)
        logger.info("Milvus 集合已删除：%s", name)

    _ready = False
    ensure_collection()


def _write_chunks(chunks: list[dict], vectors: list[list[float]]) -> dict:

    client = get_client()
    name = settings.MILVUS_COLLECTION
    ensure_collection()

    # 先按 source 删除旧分块，再插入新的
    # 文件变短、分块变少时不会残留上一次的旧片段
    sources = sorted({chunk["metadata"]["source"] for chunk in chunks})

    if sources:
        quoted = ", ".join('"' + s.replace('"', '\\"') + '"' for s in sources)
        client.delete(name, filter=f"source in [{quoted}]")

    rows = []
    for chunk, vector in zip(chunks, vectors):
        meta = chunk["metadata"]
        rows.append(
            {
                "id": chunk["id"],
                "vector": vector,
                "document": chunk["document"],
                "source": meta["source"],
                # Milvus 的 VARCHAR 不接受 None，空标题要写成空字符串
                "heading": meta["heading"] or "",
                "chunk": meta["chunk"],
            }
        )

    for start in range(0, len(rows), _INSERT_BATCH):
        client.insert(name, rows[start : start + _INSERT_BATCH])

    # flush 之后数据才保证落盘，search 才稳定可见
    client.flush(name)

    total = _count_rows()

    logger.info(
        "Milvus 入库完成：本次写入 %d 块，集合现有 %d 块",
        len(chunks),
        total,
    )

    return {"files": len(sources), "chunks": len(chunks), "total": total}


async def ingest(reset: bool = False) -> dict:
    chunks = await run_in_threadpool(load_chunks)
    if reset:
        await run_in_threadpool(_reset_collection)

    texts = [chunk["document"] for chunk in chunks]
    vectors = await embedding_service.embed_texts(texts)

    return await run_in_threadpool(_write_chunks, chunks, vectors)


# -----------------------------------------检索--------------------------------


def _query_sync(query_vector: list[float], top_k: int) -> list[dict]:

    client = get_client()
    name = settings.MILVUS_COLLECTION

    ensure_collection()

    results = client.search(
        collection_name=name,
        data=[query_vector],
        limit=top_k,
        output_fields=["document", "source", "heading", "chunk"],
        search_params={
            "metric_type": "COSINE",
            # ef 越大召回越准但越慢，取 top_k 的 4~8 倍比较常见
            "params": {"ef": max(64, top_k * 8)},
        },
    )

    if not results or not results[0]:
        return []

    hits: list[dict] = []

    for hit in results[0]:
        # COSINE 下 distance 字段里存的是「相似度」，越大越相关
        score = float(hit["distance"])

        # 低于阈值的直接丢掉：宁可少给资料，也不要把不相关内容塞进提示词
        if score < settings.RAG_MIN_SCORE:
            continue

        entity = hit.get("entity") or {}

        hits.append(
            {
                "document": entity.get("document", ""),
                "source": entity.get("source", ""),
                "heading": entity.get("heading", ""),
                "score": round(score, 4),
                # 顺手给出 Chroma 语义的等价距离，方便沿用旧代码/旧日志
                "distance": round(1 - score, 4),
            }
        )

    return hits


async def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    query_vector = await embedding_service.embed_query(query)

    return await run_in_threadpool(
        _query_sync, query_vector, top_k or settings.RAG_TOP_K
    )
