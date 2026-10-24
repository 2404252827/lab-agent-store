"""构建知识库向量库

在 backend 目录下执行：
    .\\.venv\\Scripts\\python.exe ingest_kb.py
"""

import asyncio

from app.services import rag_service


async def main() -> None:
    result = await rag_service.ingest()

    print(
        f"入库完成：{result['files']} 个文件，{result['chunks']} 个分块；"
        f"集合现有 {result['total']} 个分块"
    )


if __name__ == "__main__":
    asyncio.run(main())
