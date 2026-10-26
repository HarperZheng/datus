# Datus-agent 安装与二次开发指南

> 基于 [Datus-ai/Datus-agent](https://github.com/Datus-ai/Datus-agent) 官方 CLAUDE.md 与 README 整理，当前版本 v0.4.2
> 适用环境：WSL Ubuntu（项目运行平台为 Linux x86_64/aarch64 glibc 2.28+ 或 Apple Silicon macOS）

---

## 目录

1. [项目简介](#一项目简介)
2. [安装与配置](#二安装与配置)
   - 2.1 二开环境搭建
   - 2.2 LLM 配置（自建 GLM 端点）
3. [启动与对话窗口](#三启动与对话窗口)
4. [二开核心约定](#四二开核心约定)
5. [二开扩展点](#五二开扩展点)
6. [测试规则](#六测试规则)
7. [提交流程](#七提交流程)
8. [常见问题](#八常见问题)

---

## 一、项目简介

AI 驱动的数据分析智能体：Natural Language → SQL，多数据库，RAG 知识库，MCP 协议。

- **技术栈**：Python 3.12+（`requires-python = ">=3.12"`）、OpenAI Agents SDK + LiteLLM、LanceDB、FastAPI、FastMCP
- **包管理器**：uv（License: Apache-2.0）
- **入口形态**：CLI 交互 / Web 聊天 / REST API / MCP Server / IM 网关 / VS Code 插件

---

## 二、安装与配置

> 本章覆盖"把项目跑起来"的路径：先搭二开环境，再配 LLM，然后进第三章启动对话。

### 2.1 二开环境搭建

> 关键点：**conda 环境里只需要装 Python 3.12，其余所有依赖都不要用 conda/pip 装**。
> 项目用 `uv` 管理依赖（`uv sync` 按 `uv.lock` 在项目下生成独立 `.venv`），conda 唯一的作用是提供解释器。

#### 1. 创建 conda 环境

```bash
conda create -n datus -c conda-forge python=3.12 -y
conda activate datus
```

#### 2. 安装 uv 并克隆代码

```bash
pip install uv

git clone https://github.com/Datus-ai/Datus-agent.git
cd Datus-agent

# 让 uv 用当前 conda 的 python 作为 .venv 的基础解释器
uv venv --python $(which python)
uv sync
```

#### 3. 验证环境

```bash
uv run python ci/run-pr-tests.py upstream/main    # PR CI 套件（无外部依赖，不需要 API key）
uv run ruff format datus/ tests/ && uv run ruff check --fix datus/ tests/   # 格式化 + lint
```

#### 4. 日常操作

都通过 `uv run` 前缀，它会自动使用项目下的 `.venv`，**不再需要** `conda activate`：

```bash
uv run datus --datasource yunnan0508
uv run datus --web --datasource yunnan0508
```

#### 5. 注意事项

- **不要** `conda install` 或往 conda 环境里 `pip install` 项目依赖（litellm、lancedb 等），会和 uv 的 `.venv` 打架，依赖版本以 `uv.lock` 为准
- IDE（VS Code/PyCharm）解释器选**项目下的 `.venv/bin/python`**，不是 conda 的 python
- 依赖装坏了：删掉 `.venv` 重新 `uv sync` 即可
- 依赖较重（LanceDB、litellm、FastAPI 全家桶），建议在 WSL 里做，Windows 原生路径下部分存储/异步代码容易踩坑

### 2.2 LLM 配置（自建 GLM 端点）

编辑全局配置 **`~/.datus/conf/agent.yml`**（注意是 `conf` 子目录；若文件不存在就从 `conf/agent.yml.example` 复制一份），自建 OpenAI 兼容端点走 `agent.models` 自定义条目，参数直接写在配置文件里：

```yaml
agent:
  name: datus
  language: zh          # 让所有节点面向用户的自然语言输出统一为中文

  target: glm           # 默认激活的模型条目 = agent.models 下的键名

  models:
    glm:
      type: openai                                  # OpenAI 兼容接口
      base_url: http://112.49.22.42:18304/v1
      api_key: dummy
      model: GLM-5.3-Flash
```

> ⚠️ **重要**：`base_url` 只写到 `/v1`，**不带** `/chat/completions` 后缀。
> OpenAI 兼容客户端（OpenAI SDK / LiteLLM）会自动在 base_url 后拼接 `/chat/completions`；
> 如果 base_url 已包含该路径，实际请求会变成 `/v1/chat/completions/chat/completions` 导致 404。

配置说明：

| 字段 | 说明 |
|---|---|
| `target` | 字符串，指向 `models` 下的键名；未单独覆盖时所有节点默认用它 |
| `models.<key>` | 键名自定义（如 `glm`），被 `target` 和节点的 `model` 字段引用 |
| `type` | 接口类型；OpenAI 兼容端点一律填 `openai` |
| `base_url` | 接口基础地址，写到 `/v1` 为止 |
| `api_key` | 访问密钥，直接写入（本端点用 `dummy`）；官方约定也支持 `${ENV_VAR}` 环境变量替换，真实密钥时建议改走环境变量 |
| `language` | 可选；`zh` 统一回答/总结/澄清提问为中文，机器成分（SQL、路径等）保持原样 |
| `ssl_verify` | 可选；内网自签名证书时指向 CA 证书包路径，或填 `false` 关闭校验（不推荐） |

配置分两层：全局 `~/.datus/conf/agent.yml` 为主配置；项目下的 `./.datus/config.yml` 存放覆盖项（如当前激活的模型、默认数据源），由 `/model` 命令写入，只允许白名单键。

---

## 三、启动与对话窗口

所有命令加 `uv run` 前缀（源码二开模式）。Web 聊天窗口的前端**已内置**（`datus/cli/web/templates/`，由 FastAPI 直接托管），无需单独构建 React。

| # | 入口 | 命令 | 访问方式 | 适用人群 |
|---|---|---|---|---|
| ① | **CLI 交互（REPL）** | `uv run datus --datasource demo` | 终端内交互 | 数据工程师 |
| ② | **网页对话窗口** | `uv run datus --web --datasource yunnan0508 --permission-mode auto` | 浏览器打开 **http://localhost:8501** | 分析师 |
| ③ | REST API | `uv run datus-api --datasource demo` | http://localhost:8000 | 应用调用 |
| ④ | MCP Server | `uv run datus-mcp --datasource demo` | 接入 Claude Desktop / Cursor 等 MCP 客户端 | 其他智能体 |
| ⑤ | 免交互脚本模式 | `uv run datus -p "你的问题" --datasource demo` | stdout 输出 JSON | CI / 脚本管道 |

### 首次启动后的三步

进入 CLI 或 Web 界面后：

1. `/model` — 交互式选供应商和模型（选择结果写入项目下的 `./.datus/config.yml`）
2. `/datasource` — 添加数据源（SQLite / DuckDB / MySQL / PostgreSQL / StarRocks 等 21 种），`demo` 就是你在这里起的名字
3. `/init` —（可选）扫描当前项目的表结构，构建上下文

> 没配数据源也可以先体验对话：`/datasource` 里挂一个 SQLite 测试库最快。

## 四、二开必知

- **改代码即时生效**：`uv sync` 默认以可编辑模式安装本项目，改完 `datus/` 下的代码，下次 `uv run` 直接生效，不用重装
- **改 `conf/providers.yml` 时**记得同步改 `datus/conf/providers.yml`（两份：一份给打包后用，一份给源码用）
- 日志在 `~/.datus/logs/`，排错先看这里
- 会话数据在 `~/.datus/sessions/{project}/`，知识库在项目根的 `./subject/`

### 4.1 语义层 KB 重建（修改指标/YAML 后必做）

`data/{project}/datus_db/` 下的 LanceDB（`metrics.lance`、`semantic_dataset.lance`、`subject_tree.db` 等）是语义层 YAML（`subject/semantic_models/{datasource}/*.yml`）的**投影索引**，供 agent 聊天时检索指标/数据集元数据。两条读路径时效性不同：

| 读取方 | 数据来源 | 时效性 |
|---|---|---|
| dosi 语义引擎（get_metric / query_metrics） | 直读 YAML，文件变更即重建 | 永远最新 |
| agent 聊天检索（search_metrics 选指标/维度） | KB 向量索引（LanceDB） | 停留在上次显式同步 |

**因此：不走 web UI 改完 YAML 后必须重建 KB，否则 agent 检索拿旧元数据作答**。此时 dosi 引擎侧一切正常，问题只出在检索层，故障很隐蔽。

重建命令（无 LLM 调用、不联网、幂等可重跑；注意入口是 **`datus-agent`** 不是 `datus`——`datus` 是聊天/Web 入口，bootstrap-kb 挂在 agent_main 下）：

```bash
uv run datus-agent bootstrap-kb --datasource yunnan0508 --components semantic_model --kb_update_strategy sync-yaml
```

- **web UI 保存免手动**：在 web 界面里编辑并保存语义文件，保存动作本身就完成了"校验 YAML → 写文件 → 同步 KB → 更新同步状态"整条链，不需要再手动跑 `uv run datus-agent bootstrap-kb`；若保存后提示 `saved_not_synced`（YAML 已存但 KB 同步失败），重试保存或手动跑命令
- **何时必须重跑**：不走 web UI 的 YAML 修改（IDE/脚本/git/agent 工具）之后；删过 `datus_db/` 之后
- `--components metadata` 另建表结构检索（schema_metadata/schema_value.lance，连数据库采集），与语义组件相互独立，按需重建
- 同步状态记录在 `datus_db` 同级的 `semantic_sync_state.json`（每个 YAML 文件的内容 SHA），可用于判断索引是否过期；同步成功会输出 `Synced N semantic YAML file(s)`

---

## 五、二开核心约定

### 代码规范

- ruff 格式化，行宽 **120**；类型注解全覆盖，数据结构用 Pydantic
- 日志用 `from datus.utils.loggings import get_logger`，**禁止 `print()`**
- 错误统一抛 `DatusException(ErrorCode.XXX)`（来自 `datus/utils/exceptions`），错误码分段：

  | 段 | 含义 |
  |---|---|
  | 1xxxxx | 通用 |
  | 2xxxxx | 节点 |
  | 3xxxxx | 模型 |
  | 4xxxxx | 工具/存储 |
  | 5xxxxx | 数据库 |
  | 6xxxxx | 语义 |

- 代码 / 注释 / commit / PR 文本只用英文；中文只允许出现在面向中国用户的文档
- CLI 输出统一走 `datus/cli/cli_styles.py` 的 `print_*` 辅助函数（`print_error` / `print_success` / `print_warning` / `print_info` / `print_status` / `print_usage` / `print_empty_set`），不用内联 Rich 标记
- CLI UI 约束：颜色不用 `bold`（bold 保留给标题/提示标签）；Unicode `✓`/`✗` 代替 emoji；闭合标签用短形式 `[/]`；表格用 `header_style=TABLE_HEADER_STYLE`；代码渲染用 `CODE_THEME = "monokai"`

### 护栏（红线）

- ❌ **不直接 import 数据库驱动** → 用 `ConnectorRegistry` / `db_manager_instance`
- ❌ **节点里不硬编码 LLM 调用** → 走 `LLMBaseModel`
- ❌ **CI 测试零外部依赖** → 零 API key、零网络、零预置数据
- ❌ **不硬编码密钥** → 环境变量或 `agent.yml` 里的 `${ENV_VAR}` 替换
- 新可调参数放 `agent.yml`，不写死常量

### 存储布局（重要）

- **项目级（CWD）**：`./subject/{semantic_models, sql_summaries}/`（知识库）、`./lineage/lineage.json`（表血缘）、`./.datus/skills/`（项目技能，覆盖全局）、`./.datus/config.yml`（项目覆盖配置）
- **全局（按项目分片）**：`~/.datus/sessions/{project}/{session_id}.db`、`~/.datus/data/{project}/datus_db/`（LanceDB）、`~/.datus/{conf, logs, cache, template, run, benchmark, workspace, skills}`
- `project_name` 由 CWD 推导（`agent_config.py` 的 `_normalize_project_name`，长路径加 md5 后缀）
- `agent.knowledge_base_home` 字段**已移除**，知识库固定在 `{project_root}/subject/`，该 YAML 字段会被静默忽略
- 语义层 KB（`data/{project}/datus_db/`）是 YAML 的投影索引，改 YAML 后须重建——操作细节见 §三「语义层 KB 重建」

---

## 六、二开扩展点

（待补全：原文件未提供该节正文。建议按以下方向展开——自定义数据源 Connector、自定义工具/Tool、自定义节点/Node、自定义 Provider、技能（skills）扩展、MCP 工具接入等，每项说明注册位置、接口约定与最小示例。）

---

## 七、常见问题

（待补全：原文件未提供该节正文。可优先收录——`base_url` 多拼 `/chat/completions` 导致 404、依赖与 conda 混装打架、IDE 解释器选错、改 YAML 后 agent 检索仍是旧元数据（需重建 KB）、`saved_not_synced` 处理、web 端口 8501 被占用等。）