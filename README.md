# Lab Agent

Lab Agent 是一个实验室智能助手系统，提供实验室与设备管理、预约审核、用户管理、文件上传以及基于大语言模型和知识库检索的 AI 对话能力。

## 功能概览

- 用户注册、登录、JWT 鉴权与管理员权限控制
- 实验室信息和设备信息的分页查询、新增、修改与删除
- 实验室预约、冲突校验、取消、审核和过期预约自动清理
- 用户资料、头像、密码及后台用户管理
- 图片和文档上传，上传文件通过 `/uploads` 提供访问
- AI 流式对话、对话历史管理，以及实验室、设备、预约和规则查询工具
- Markdown 知识库切分、向量化并写入 Milvus，供 RAG 检索使用

## 技术栈

| 层级 | 主要技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Vue Router、Element Plus、Axios |
| 后端 | Python、FastAPI、SQLAlchemy Async、Pydantic |
| 业务数据库 | MySQL |
| 对话历史数据库 | PostgreSQL |
| 向量数据库 | Milvus |
| AI 能力 | DeepSeek 对话模型、LangChain/LangGraph、SiliconFlow 嵌入模型 |

## 系统架构

```text
浏览器
  │
  ▼
Vue 3 页面（views + scripts）
  │  调用
  ▼
前端 API 封装（src/api + src/utils/request.js）
  │  HTTP / SSE
  ▼
FastAPI 路由（backend/app/api）
  │
  ▼
业务服务层（backend/app/services）
  ├── MySQL：用户、实验室、设备、预约
  ├── PostgreSQL：AI 对话历史
  ├── Milvus：知识库向量
  └── DeepSeek / SiliconFlow：对话与嵌入模型
```

### 后端分层约定

1. `api/` 只负责接收请求、注入依赖和返回统一响应。
2. `services/` 承载业务校验、数据库操作和外部服务调用。
3. `models/` 定义数据库表，`schemas/` 定义请求与响应结构。
4. `common/` 提供统一响应、异常处理和中间件。
5. `dependencies/`、`utils/` 提供鉴权、JWT 和密码工具。

### 推荐阅读顺序

1. `backend/app/main.py`：应用入口、中间件、路由挂载和启动任务。
2. `backend/app/api/`：了解系统对外接口。
3. `backend/app/services/`：了解核心业务逻辑。
4. `backend/app/models/` 和 `backend/app/schemas/`：了解数据结构。
5. `frontend/src/router/index.js`：了解前端页面与访问权限。
6. `frontend/src/views/` 和 `frontend/src/scripts/`：了解页面结构与交互逻辑。
7. `frontend/src/api/`：了解前后端接口对应关系。

## 项目结构

```text
lab-agent/
├── .gitignore                              # 排除依赖、密钥、构建产物、上传文件等本地内容
├── README.md                               # 项目总览、架构、目录说明与启动指南
│
├── backend/
│   ├── .env.example                        # 后端环境变量模板
│   ├── requirements.txt                    # Python 依赖清单
│   ├── _smoke.py                           # 预约接口冒烟测试，运行后清理测试数据
│   ├── ingest_kb.py                        # 将 data/kb 中的 Markdown 知识库写入 Milvus
│   ├── seed_demo_data.py                   # 幂等生成用户、实验室和设备演示数据
│   │
│   ├── app/
│   │   ├── __init__.py                     # 后端 app 包标识
│   │   ├── config.py                       # 环境变量、上传目录、知识库目录等全局配置
│   │   ├── database.py                     # MySQL 异步引擎、会话工厂和业务模型基类 Base
│   │   ├── pg_database.py                  # PostgreSQL 异步引擎、会话工厂和聊天模型基类 PgBase
│   │   ├── main.py                         # FastAPI 入口，注册中间件、路由、启动建表和静态目录
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py                 # 汇总所有业务路由并统一挂载到 /api
│   │   │   ├── auth.py                     # 登录、注册接口
│   │   │   ├── files.py                    # 文件上传接口
│   │   │   ├── user.py                     # 当前用户资料、密码及管理员用户管理接口
│   │   │   ├── lab.py                      # 实验室列表、新增、修改、删除接口
│   │   │   ├── equipment.py                # 设备列表、新增、修改、删除接口
│   │   │   ├── reservation.py              # 预约创建、列表、占用日期、取消和审核接口
│   │   │   └── ai.py                       # AI 普通对话、流式对话和历史记录接口
│   │   │
│   │   ├── common/
│   │   │   ├── __init__.py                 # common 包标识
│   │   │   ├── exceptions.py               # 业务异常及 HTTP、参数校验、全局异常处理器
│   │   │   ├── middlewares.py              # 捕获未处理异常并返回带 CORS 头的 500 响应
│   │   │   └── response.py                 # 统一响应结构 Response 和分页结构 PageResponse
│   │   │
│   │   ├── dependencies/
│   │   │   ├── __init__.py                 # dependencies 包标识
│   │   │   └── auth.py                     # 从 JWT 获取当前用户、管理员权限依赖
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py                 # models 包标识
│   │   │   ├── chat.py                     # PostgreSQL 对话消息表 ChatMessageRecord
│   │   │   ├── user.py                     # 用户表 User
│   │   │   ├── lab.py                      # 实验室表 Lab
│   │   │   ├── equipment.py                # 设备表 Equipment，并关联所属实验室
│   │   │   └── reservation.py              # 预约表 Reservation，并关联用户和实验室
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py                 # schemas 包标识
│   │   │   ├── auth.py                     # 登录和注册请求/响应模型
│   │   │   ├── user.py                     # 用户响应、资料更新、密码更新和创建模型
│   │   │   ├── lab.py                      # 实验室创建、更新、响应及时间格式校验
│   │   │   ├── equipment.py                # 设备创建、更新、响应及图片字段校验
│   │   │   ├── reservation.py              # 预约创建、更新、响应及日期时间校验
│   │   │   ├── file.py                     # 文件上传响应模型
│   │   │   └── ai.py                       # AI 请求、响应和历史消息模型
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py                 # services 包标识
│   │   │   ├── auth_service.py             # 登录校验、注册和用户初始化逻辑
│   │   │   ├── user_service.py             # 用户资料、密码及管理员用户 CRUD 业务
│   │   │   ├── lab_service.py              # 实验室 CRUD、名称唯一性和开放时间校验
│   │   │   ├── equipment_service.py        # 设备 CRUD、关联实验室和状态处理
│   │   │   ├── reservation_service.py      # 预约冲突校验、审核、取消及过期自动取消任务
│   │   │   ├── embedding_service.py        # 调用 SiliconFlow 生成文本向量
│   │   │   ├── rag_service.py              # Markdown 切分、Milvus 建库入库和相似度检索
│   │   │   ├── chat_history_service.py     # PostgreSQL 对话历史的读取、保存和清空
│   │   │   ├── agent_tools.py              # AI 可调用的实验室、设备、预约和规则查询工具
│   │   │   └── agent_service.py            # LangGraph 对话代理、上下文加载、回答与流式输出
│   │   │
│   │   └── utils/
│   │       ├── __init__.py                 # utils 包标识
│   │       ├── jwt.py                      # JWT 创建与解析
│   │       └── password.py                 # bcrypt 密码哈希与校验
│   │
│   └── data/
│       └── kb/
│           ├── 01-实验室预约规则.md          # 预约时间、冲突和取消规则知识库
│           ├── 02-实验室信息说明.md          # 实验室字段、状态和使用说明知识库
│           ├── 03-设备管理说明.md            # 设备状态、容量和管理规则知识库
│           ├── 04-用户与权限说明.md          # 用户角色、资料和管理权限知识库
│           ├── 05-文件上传说明.md            # 上传格式、大小限制和访问方式知识库
│           └── 06-系统概述与常见问题.md      # 系统功能概述和常见问题知识库
│
└── frontend/
    ├── .env.development                    # 前端开发环境变量，配置后端服务地址
    ├── .gitignore                          # 前端依赖、构建产物和编辑器文件忽略规则
    ├── .prettierrc.json                    # Prettier 代码格式规范
    ├── README.md                           # Vite/Vue 前端模板使用说明
    ├── index.html                          # 单页应用 HTML 入口和挂载节点
    ├── jsconfig.json                       # JavaScript 配置及 @ 到 src 的路径别名
    ├── package.json                        # 前端依赖、Node 版本和 npm 脚本
    ├── package-lock.json                   # npm 依赖锁定文件
    ├── vite.config.js                      # Vite 插件、路径别名和开发代理配置
    │
    ├── public/
    │   └── favicon.ico                     # 浏览器站点图标
    │
    └── src/
        ├── App.vue                         # Vue 根组件，承载顶层 router-view
        ├── main.js                         # 创建 Vue 应用，注册路由、Element Plus、中文语言包和图标
        │
        ├── api/
        │   ├── auth.js                     # 登录、注册接口封装
        │   ├── user.js                     # 个人资料、密码及用户管理接口封装
        │   ├── lab.js                      # 实验室 CRUD 接口封装
        │   ├── equipment.js                # 设备 CRUD 接口封装
        │   ├── reservation.js              # 预约创建、查询、取消和审核接口封装
        │   ├── file.js                     # 文件上传和服务器文件 URL 解析
        │   └── ai.js                       # AI 历史、普通对话、SSE 流式对话及工具状态文案
        │
        ├── assets/
        │   └── css/
        │       ├── global.css              # 全局基础样式、变量和通用布局规则
        │       ├── auth.css                # 登录与注册页面样式
        │       ├── ai.css                  # AI 对话页样式
        │       ├── lab.css                 # 实验室管理页样式
        │       ├── equipment.css           # 设备管理页样式
        │       ├── reservation.css         # 预约管理页样式
        │       ├── user.css                # 用户管理页样式
        │       ├── profile.css             # 个人资料页样式
        │       └── password.css            # 修改密码页样式
        │
        ├── layouts/
        │   ├── Layout.vue                  # 登录后的后台整体布局、侧边导航、顶栏和子路由出口
        │   └── Layout.css                  # 后台布局、折叠菜单和移动端抽屉样式
        │
        ├── router/
        │   └── index.js                    # 全部页面路由、懒加载、登录守卫和管理员权限守卫
        │
        ├── scripts/
        │   ├── login.js                    # 登录页面状态、提交和跳转逻辑
        │   ├── register.js                 # 注册页面表单校验和提交逻辑
        │   ├── layout.js                   # 侧边栏折叠、移动端菜单、用户菜单和退出登录逻辑
        │   ├── ai.js                       # AI 对话历史、流式发送、工具提示和滚动逻辑
        │   ├── lab.js                      # 实验室 CRUD、图片上传和实验室预约逻辑
        │   ├── equipment.js                # 设备 CRUD、筛选、图片上传和实验室关联逻辑
        │   ├── reservation.js              # 预约分页筛选、状态展示、取消和审核逻辑
        │   ├── user.js                     # 管理员用户 CRUD、头像上传和字段校验逻辑
        │   ├── profile.js                  # 当前用户资料加载、更新和头像上传逻辑
        │   └── password.js                 # 修改密码表单校验和提交逻辑
        │
        ├── utils/
        │   ├── auth.js                     # Token/用户信息读写、登录态更新和清理
        │   └── request.js                  # Axios 实例、Token 注入、统一响应和 401 处理
        │
        └── views/
            ├── Login.vue                   # 登录页模板
            ├── Register.vue                # 注册页模板
            ├── Home.vue                    # 系统首页
            ├── Ai.vue                      # AI 智能助手对话页
            ├── Lab.vue                     # 实验室管理页
            ├── Equipment.vue               # 设备管理页
            ├── Reservation.vue             # 预约管理页
            ├── User.vue                    # 管理员用户管理页
            ├── Profile.vue                 # 个人信息页
            └── Password.vue                # 修改密码页
```

> `views/` 只保留页面模板，具体交互逻辑位于同名或对应的 `scripts/` 文件中；组件通过 `<script src="../scripts/*.js">` 复用这些逻辑。

## 数据存储说明

| 数据 | 存储位置 | 入口 |
| --- | --- | --- |
| 用户、实验室、设备、预约 | MySQL | `backend/app/database.py` |
| AI 对话历史 | PostgreSQL | `backend/app/pg_database.py` |
| 知识库向量 | Milvus | `backend/app/services/rag_service.py` |
| 知识库原文 | `backend/data/kb/` | `backend/ingest_kb.py` |
| 用户上传文件 | 本地 `backend/uploads/` | `backend/app/api/files.py` |

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

如需导入知识库：

```powershell
cd backend
python ingest_kb.py
```

如需生成演示数据：

```powershell
cd backend
python seed_demo_data.py
```

## 前端启动

要求 Node.js 22.18+ 或 24.12+。

```powershell
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`。默认后端地址可在 `frontend/.env.development` 中通过 `VITE_API_BASE_URL` 修改。

生产构建：

```powershell
cd frontend
npm run build
```
