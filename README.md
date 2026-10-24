# Lab Agent

实验室智能助手项目，前端使用 Vue 3 + Vite，后端使用 FastAPI，并结合大语言模型、Milvus 向量检索及关系型数据库提供实验室、设备、预约、用户和 AI 对话能力。

## 项目结构

```text
lab-agent/
├── backend/   # FastAPI 后端
└── frontend/  # Vue 3 + Vite 前端
```

## 后端启动

要求 Python 3.11+，并准备 MySQL、PostgreSQL 和 Milvus 服务。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，填写数据库、JWT、模型和 Milvus 配置
uvicorn app.main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`，接口文档位于 `http://127.0.0.1:8000/docs`。

如需导入 `backend/data/kb` 中的知识库文档：

```powershell
python ingest_kb.py
```

## 前端启动

要求 Node.js 22.18+ 或 24.12+。

```powershell
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`。默认后端地址可在 `frontend/.env.development` 中通过 `VITE_API_BASE_URL` 修改。

## 安全说明

`backend/.env`、本地虚拟环境、前端依赖目录、构建产物和用户上传文件均已在 `.gitignore` 中排除。请勿把真实密钥、数据库密码或用户文件提交到 Git 仓库。
