from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 后端项目路径
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    # ---- AI 对话历史（独立 PostgreSQL）----
    PG_DATABASE_URL: str = (
        "postgresql+asyncpg://lab_agent:lab_agent_pwd@127.0.0.1:5432/lab_agent_chat"
    )
    # 送给模型的最近消息条数（user + assistant 合计）
    CHAT_CONTEXT_LIMIT: int = 20
    # 历史接口返回给前端的最多消息条数
    CHAT_PAGE_LIMIT: int = 100

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-flash"
    AI_TEMPERATURE: float | None = None
    AI_MAX_TOKENS: int = 2048

    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_EMBED_MODEL: str = "BAAI/bge-m3"
    EMBED_DIM: int = 1024
    EMBED_BATCH_SIZE: int = 16

    RAG_TOP_K: int = 4
    RAG_MAX_CHUNK_CHARS: int = 800

    MILVUS_URI: str = "http://127.0.0.1:19530"
    MILVUS_TOKEN: str = ""
    MILVUS_DB_NAME: str = ""
    MILVUS_COLLECTION: str = "lab_kb"
    RAG_MIN_SCORE: float = 0.5

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()

# 静态资源存放地址
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100M

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}

# RAG 用到的目录
CHROMA_DIR = BASE_DIR / "data" / "chroma"  # 向量库存放地址，由 Chroma 自动创建
KB_DIR = BASE_DIR / "data" / "kb"  # 知识库文档
KB_DIR.mkdir(parents=True, exist_ok=True)
