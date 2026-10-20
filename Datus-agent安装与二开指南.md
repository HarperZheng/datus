# Datus-agent 安装与二次开发指南

> 基于 [Datus-ai/Datus-agent](https://github.com/Datus-ai/Datus-agent) 官方 CLAUDE.md 与 README 整理,当前版本 v0.4.2
> 适用环境:WSL Ubuntu(项目运行平台为 Linux x86_64/aarch64 glibc 2.28+ 或 Apple Silicon macOS)

---

## 目录

1. [项目简介](#一项目简介)
2. [普通安装(只使用)](#二普通安装只使用)
3. [二开环境搭建](#三二开环境搭建)
4. [LLM 配置(自建 GLM 端点)](#四llm-配置自建-glm-端点)
5. [启动与对话窗口](#五启动与对话窗口)
6. [二开核心约定](#六二开核心约定)
7. [二开扩展点](#七二开扩展点)
8. [测试规则](#八测试规则)
9. [提交流程](#九提交流程)
10. [常见问题](#十常见问题)

---

## 一、项目简介

AI 驱动的数据分析智能体:Natural Language → SQL,多数据库,RAG 知识库,MCP 协议。

- **技术栈**:Python 3.12+(`requires-python = ">=3.12"`)、OpenAI Agents SDK + LiteLLM、LanceDB、FastAPI、FastMCP
- **包管理器**:uv(License: Apache-2.0)
- **入口形态**:CLI 交互 / Web 聊天 / REST API / MCP Server / IM 网关 / VS Code 插件

---

## 二、普通安装(只使用)

```bash
# 方式 1:一键脚本
curl -fsSL https://raw.githubusercontent.com/datus-ai/datus-agent/main/install.sh | sh

# 方式 2:pip(国内网络 pip 在 litellm 上回溯很慢时,用 uv)
pip install uv && uv pip install datus-agent --system
```

装完开新 shell 运行 `datus`,然后三步配置:

1. `/model` — 配置 LLM
2. `/datasource` — 添加数据源
3. `/init` —(可选)扫描当前项目

---

## 三、二开环境搭建

> 关键点:**conda 环境里只需要装 Python 3.12,其余所有依赖都不要用 conda/pip 装**。
> 项目用 `uv` 管理依赖(`uv sync` 按 `uv.lock` 在项目下生成独立 `.venv`),conda 唯一的作用是提供解释器。

### 1. 创建 conda 环境

```bash
conda create -n datus -c conda-forge python=3.12 -y
conda activate datus
```

> 如遇 `CondaToSNonInteractiveError`(新版 conda 要求接受 Anaconda 官方源服务条款),二选一:
>
> ```bash
> # 办法 1:直接接受条款
> conda tos accept --override-channels \
>   --channel https://repo.anaconda.com/pkgs/main \
>   --channel https://repo.anaconda.com/pkgs/r
>
> # 办法 2:改用 conda-forge 源(无条款限制,推荐)
> conda create -n datus -c conda-forge python=3.12 -y
> # 国内网络慢可用清华镜像:
> conda create -n datus -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge python=3.12 -y
> ```

### 2. 安装 uv 并克隆代码

```bash
pip install uv

git clone https://github.com/Datus-ai/Datus-agent.git
cd Datus-agent

# 让 uv 用当前 conda 的 python 作为 .venv 的基础解释器
uv venv --python $(which python)
uv sync
```

### 3. 验证环境

```bash
uv run python ci/run-pr-tests.py upstream/main    # PR CI 套件(无外部依赖,不需要 API key)
uv run ruff format datus/ tests/ && uv run ruff check --fix datus/ tests/   # 格式化 + lint
```

### 4. 日常操作

都通过 `uv run` 前缀,它会自动使用项目下的 `.venv`,**不再需要** `conda activate`:

```bash
uv run pytest tests/unit_tests/ -x
uv run ruff format datus/ tests/
uv run datus --datasource demo
uv run datus --web --datasource yunnan0508
```

### 5. 注意事项

- **不要** `conda install` 或往 conda 环境里 `pip install` 项目依赖(litellm、lancedb 等),会和 uv 的 `.venv` 打架,依赖版本以 `uv.lock` 为准
- IDE(VS Code/PyCharm)解释器选**项目下的 `.venv/bin/python`**,不是 conda 的 python
- 依赖装坏了:删掉 `.venv` 重新 `uv sync` 即可
- 依赖较重(LanceDB、litellm、FastAPI 全家桶),建议在 WSL 里做,Windows 原生路径下部分存储/异步代码容易踩坑

---

## 四、LLM 配置(自建 GLM 端点)

### agent.yml 配置

编辑全局配置 **`~/.datus/conf/agent.yml`**(注意是 `conf` 子目录;若文件不存在就从 `conf/agent.yml.example` 复制一份),自建 OpenAI 兼容端点走 `agent.models` 自定义条目,参数直接写在配置文件里:

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

> ⚠️ **重要**:`base_url` 只写到 `/v1`,**不带** `/chat/completions` 后缀。
> OpenAI 兼容客户端(OpenAI SDK / LiteLLM)会自动在 base_url 后拼接 `/chat/completions`;
> 如果 base_url 已包含该路径,实际请求会变成 `/v1/chat/completions/chat/completions` 导致 404。

配置说明:

| 字段 | 说明 |
|---|---|
| `target` | 字符串,指向 `models` 下的键名;未单独覆盖时所有节点默认用它 |
| `models.<key>` | 键名自定义(如 `glm`),被 `target` 和节点的 `model` 字段引用 |
| `type` | 接口类型;OpenAI 兼容端点一律填 `openai` |
| `base_url` | 接口基础地址,写到 `/v1` 为止 |
| `api_key` | 访问密钥,直接写入(本端点用 `dummy`);官方约定也支持 `${ENV_VAR}` 环境变量替换,真实密钥时建议改走环境变量 |
| `language` | 可选;`zh` 统一回答/总结/澄清提问为中文,机器成分(SQL、路径等)保持原样 |
| `ssl_verify` | 可选;内网自签名证书时指向 CA 证书包路径,或填 `false` 关闭校验(不推荐) |

配置分两层:全局 `~/.datus/conf/agent.yml` 为主配置;项目下的 `./.datus/config.yml` 存放覆盖项(如当前激活的模型、默认数据源),由 `/model` 命令写入,只允许白名单键。

---

## 五、启动与对话窗口

所有命令加 `uv run` 前缀(源码二开模式)。Web 聊天窗口的前端**已内置**(`datus/cli/web/templates/`,由 FastAPI 直接托管),无需单独构建 React。

| # | 入口 | 命令 | 访问方式 | 适用人群 |
|---|---|---|---|---|
| ① | **CLI 交互(REPL)** | `uv run datus --datasource demo` | 终端内交互 | 数据工程师 |
| ② | **网页对话窗口** | `uv run datus --web --datasource yunnan0508 --permission-mode auto` | 浏览器打开 **http://localhost:8501** | 分析师 |
| ③ | REST API | `uv run datus-api --datasource demo` | http://localhost:8000 | 应用调用 |
| ④ | MCP Server | `uv run datus-mcp --datasource demo` | 接入 Claude Desktop / Cursor 等 MCP 客户端 | 其他智能体 |
| ⑤ | 免交互脚本模式 | `uv run datus -p "你的问题" --datasource demo` | stdout 输出 JSON | CI / 脚本管道 |

### 首次启动后的三步

进入 CLI 或 Web 界面后:

1. `/model` — 交互式选供应商和模型(选择结果写入项目下的 `./.datus/config.yml`)
2. `/datasource` — 添加数据源(SQLite / DuckDB / MySQL / PostgreSQL / StarRocks 等 21 种),`demo` 就是你在这里起的名字
3. `/init` —(可选)扫描当前项目的表结构,构建上下文

> 没配数据源也可以先体验对话:`/datasource` 里挂一个 SQLite 测试库最快。

### 二开必知

- **改代码即时生效**:`uv sync` 默认以可编辑模式安装本项目,改完 `datus/` 下的代码,下次 `uv run` 直接生效,不用重装
- **改 `conf/providers.yml` 时**记得同步改 `datus/conf/providers.yml`(两份:一份给打包后用,一份给源码用)
- 日志在 `~/.datus/logs/`,排错先看这里
- 会话数据在 `~/.datus/sessions/{project}/`,知识库在项目根的 `./subject/`

### 对话链路源码入口

二开对话功能,重点读这两个文件:

- `datus/cli/web/chatbot.py` — Web 对话窗口入口
- `datus/agent/node/chat_agentic_node.py` — 对话节点

---

## 六、二开核心约定

### 代码规范

- ruff 格式化,行宽 **120**;类型注解全覆盖,数据结构用 Pydantic
- 日志用 `from datus.utils.loggings import get_logger`,**禁止 `print()`**
- 错误统一抛 `DatusException(ErrorCode.XXX)`(来自 `datus/utils/exceptions`),错误码分段:

  | 段 | 含义 |
  |---|---|
  | 1xxxxx | 通用 |
  | 2xxxxx | 节点 |
  | 3xxxxx | 模型 |
  | 4xxxxx | 工具/存储 |
  | 5xxxxx | 数据库 |
  | 6xxxxx | 语义 |

- 代码 / 注释 / commit / PR 文本只用英文;中文只允许出现在面向中国用户的文档
- CLI 输出统一走 `datus/cli/cli_styles.py` 的 `print_*` 辅助函数(`print_error` / `print_success` / `print_warning` / `print_info` / `print_status` / `print_usage` / `print_empty_set`),不用内联 Rich 标记
- CLI UI 约束:颜色不用 `bold`(bold 保留给标题/提示标签);Unicode `✓`/`✗` 代替 emoji;闭合标签用短形式 `[/]`;表格用 `header_style=TABLE_HEADER_STYLE`;代码渲染用 `CODE_THEME = "monokai"`

### 护栏(红线)

- ❌ **不直接 import 数据库驱动** → 用 `ConnectorRegistry` / `db_manager_instance`
- ❌ **节点里不硬编码 LLM 调用** → 走 `LLMBaseModel`
- ❌ **CI 测试零外部依赖** → 零 API key、零网络、零预置数据
- ❌ **不硬编码密钥** → 环境变量或 `agent.yml` 里的 `${ENV_VAR}` 替换
- 新可调参数放 `agent.yml`,不写死常量

### 存储布局(重要)

- **项目级(CWD)**:`./subject/{semantic_models, sql_summaries}/`(知识库)、`./lineage/lineage.json`(表血缘)、`./.datus/skills/`(项目技能,覆盖全局)、`./.datus/config.yml`(项目覆盖配置)
- **全局(按项目分片)**:`~/.datus/sessions/{project}/{session_id}.db`、`~/.datus/data/{project}/datus_db/`(LanceDB)、`~/.datus/{conf, logs, cache, template, run, benchmark, workspace, skills}`
- `project_name` 由 CWD 推导(`agent_config.py` 的 `_normalize_project_name`,长路径加 md5 后缀)
- `agent.knowledge_base_home` 字段**已移除**,知识库固定在 `{project_root}/subject/`,该 YAML 字段会被静默忽略

---

## 七、二开扩展点

| 想做什么 | 怎么做 |
|---|---|
| **新增 Agent 节点** | 在 `datus/agent/node/` 建文件,继承 `Node` 或 `AgenticNode`;在 `datus/configuration/node_type.py` 注册类型;在 `Node.new_instance()`(`node.py`)加工厂映射 |
| **新增 LLM 供应商**(现有接口) | 只需在 `conf/providers.yml` 和 `datus/conf/providers.yml` 加条目,可选加 `model_specs`,**不用写 Python** |
| **新增 LLM 模型**(新 SDK/鉴权) | 在 `datus/models/` 建文件,继承 `LLMBaseModel`(`base.py`),注册 `MODEL_TYPE_MAP`,加到 `tests/regression/test_regression_llm.py` 的 `PROVIDER_MODELS` |
| **新增 MCP 工具** | 在 `datus/tools/func_tool/` 写函数,注册到 MCP server 工具列表 |

> 不动核心的另一条路:写**插件**(plugin)。用 `datus-plugin.yml` 声明 CLI 命令、skills 和 prompt 上下文,按项目激活,参考官方插件开发指南(docs.datus.ai → plugin/development)。

---

## 八、测试规则

### 三层测试,mock 策略不同

| 层 | marker | 要求 |
|---|---|---|
| CI | (PR harness + 受影响单测) | <5s/条,确定性,**必须** mock 所有外部调用(LLM、远程 DB、网络、可选包) |
| Nightly | `@pytest.mark.nightly` | 可用真实 LLM API;mock 不稳定服务 |
| Regression | `@pytest.mark.regression` | 真实服务;缺 key 用 `@pytest.mark.skipif` 跳过 |

CI 在不装可选包(`datus-bi-superset`、`datus-bi-grafana` 等)的环境下运行;涉及这些包的测试必须在装/不装两种情况下都能通过。(`datus-bi-core` 是硬依赖,始终可用。)

### 文件命名与位置

| 位置 | 规则 |
|---|---|
| `tests/unit_tests/` | `test_{module}.py`,**镜像源码路径**:`datus/a/b/c.py` → `tests/unit_tests/a/b/test_c.py` |
| `tests/integration/` | `test_{scenario}.py` |
| `tests/regression/` | `test_regression_{dimension}.py` |

新增子目录要创建中间 `__init__.py`。常用模式:缺 API key 用 `@pytest.mark.skipif(not os.getenv("KEY"), reason=...)`;跨数据库参数化用 `@pytest.mark.parametrize("db_type", [DBType.SQLITE, DBType.DUCKDB])`。

### 改动这些模块时必跑的额外测试

| 修改的模块 | 额外测试 |
|---|---|
| `datus/models/{provider}_model.py` | `integration/models/test_*_model.py`、`regression/test_regression_llm.py` |
| `datus/agent/node/` | `unit_tests/agent/node/test_node.py`、`test_schema_linking.py`、`test_date_parser_*.py` |
| `datus/cli/repl.py` | `integration/cli/test_cli_commands.py`、`regression/test_regression_web_e2e.py` |
| `datus/tools/func_tool/` | `integration/tools/test_func_tools_db.py`、`integration/tools/test_mcp_server.py` |
| `datus/tools/skill_tools/` | `unit_tests/tools/skill_tools/test_skill_*.py` |
| `datus/tools/permission/` | `unit_tests/tools/permission/test_permission_*.py` |
| `datus/mcp_server.py` | `unit_tests/test_mcp_server.py`、`integration/tools/test_mcp_server.py` |
| `datus/storage/reference_template/` | `unit_tests/storage/reference_template/test_*.py`、`integration/tools/test_reference_template.py` |
| `datus/storage/document/` | `integration/storage/test_doc_search.py`、`integration/storage/test_platform_doc.py` |

### 测试质量(超出覆盖率的要求)

除 happy path 外还要覆盖:输入格式变体(所有合法形态)、返回类型契约(每个分支返回相同结构)、跨组件契约(消费生产方的真实输出)、正则/SQL/路径沙箱的对抗输入、深度 ≥3 的递归/嵌套结构、标准规范符合性(`.gitignore`、SQL 方言)。

### BugFix 回归测试

- **先红后绿**:BugFix PR 新增的测试必须在未修复代码上失败。验证方式:`git stash push -- <改动文件>` → 跑测试 → `git stash pop`,或在修复前 commit 的 worktree 上跑,并在 PR 的 `## Test Cases` 里说明
- **断言性质而非实例**:钉住 bug 违反的不变量,而不是修复后碰巧产出的值(如"任何二进制源类型都不得映射为 VARBINARY",而非"BYTEA 映射为 STRING"),这样 bug 换个形态回归时测试依然能抓住

### 删代码时不留墓碑测试

删除代码时更新/删除覆盖它的既有测试,**不要**新增"断言代码不存在"的测试(`not hasattr(...)`、`"xxx" not in source`、import 失败检查)——这类测试钉死实现细节,抓不到真实 bug,还会破坏未来合法重构。

例外:删除本身是外部契约时,加一个断言**行为**不再发生的回归测试,并在测试里注明保护的契约。合格场景:废弃的公共 API/配置字段(如被移除的 YAML key 必须被静默忽略)、安全修复(密钥不得出现在日志)、有真实回归风险的副作用移除(mock 上 `assert_not_called`)。

---

## 九、提交流程

每个 PR 都要过以下关卡:

```bash
# 1. 格式化(CI 用 ruff format --check / ruff check 检查同样路径)
uv run ruff format datus/ tests/ && uv run ruff check --fix datus/ tests/

# 2. PR 覆盖率套件:验收测试 + 受影响单测 + Cobertura 覆盖率 + diff 覆盖率
#    失败时查看 ci/test-report.md 和 ci/diff-cover-report.md
uv run python ci/run-pr-tests.py upstream/main

# 3. 测试质量审计:必须 P0=0(P0 硬失败;P1 仅警告但应处理)
#    改了很多测试文件时用 --all 全量扫描
uv run python ci/audit_tests.py --repo-root . --diff-only upstream/main

# 4. 合并队列演练(改动验收 harness 目标、CI 脚本或影响 merge-queue 集成覆盖时)
uv run python ci/run-merge-queue-tests.py
```

### PR 标题

必须以下列前缀之一开头,否则 CI 拒收:

`[BugFix]` `[Enhancement]` `[Feature]` `[Refactor]` `[UT]` `[Doc]` `[Tool]` `[Others]`

### PR 正文

严格使用 `.github/PULL_REQUEST_TEMPLATE.md`,三段缺一不可:

1. **`## Why`** — 解决什么问题,有关联 issue 就链接
2. **`## Solution`** — 方案、关键决策、取舍
3. **`## Test Cases`** — 新增/修改的集成/夜间测试;没有就说明理由。BugFix PR 还要说明新测试在修复前的代码上会失败

用 `gh pr create --body` 时,以模板文件为起点。缺段的 PR 会在 review 前被要求修改。

### 其他

- pre-commit hooks:**禁止 `--no-verify`**,自动修复后重试直到通过
- 只 push 到 `origin`,**绝不 push 到 `upstream`**

---

## 十、常见问题

**Q: uv sync 报错 litellm 解析慢/失败?**
A: README 明确提示 pip 在 litellm 版本回溯上可能花数分钟(≤0.3.9 受影响),uv 几秒就能解析同一依赖集,坚持用 `uv sync`。

**Q: 内网 LLM 网关报 SSL 证书错误?**
A: `agent.models.<key>` 里加 `ssl_verify: /path/to/ca.pem`(信任私有 CA),或直接内联证书内容;不推荐 `ssl_verify: false`。优先级:`ssl_verify` → `SSL_VERIFY` 环境变量 → `SSL_CERT_FILE` 环境变量 → certifi 默认。

**Q: `(base)` 前缀干扰终端?**
A: `conda config --set auto_activate_base false`。

**Q: Windows 下跑测试有 event-loop 报错?**
A: 项目在 `datus/utils/async_utils.py` 提供了事件循环辅助工具(尤其针对 Windows);但建议整体开发放 WSL。

**Q: 想本地跑 Web 窗口但端口占用?**
A: Web 聊天默认 8501,REST API 默认 8000;冲突时释放端口或查 CLI 启动参数改端口。

---

## 附:二开推荐顺序

1. 按 [三、二开环境搭建](#三二开环境搭建) 装好环境,跑通 `ci/run-pr-tests.py`
2. 按 [四、LLM 配置](#四llm-配置自建-glm-端点) 配好 GLM 端点
3. 按 [五、启动与对话窗口](#五启动与对话窗口) 跑通 Web 窗口(http://localhost:8501)
4. 通读 `datus/cli/web/chatbot.py` 和 `datus/agent/node/chat_agentic_node.py`,掌握对话主链路
5. 按 [七、二开扩展点](#七二开扩展点) 选择扩展方向动工
6. 提交前按 [九、提交流程](#九提交流程) 过全部关卡
