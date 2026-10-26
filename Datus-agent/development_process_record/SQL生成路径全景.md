# Datus SQL 生成路径全景

> **目的**：回答"datus 里一条 SQL 到底怎么出生的"——两条主通道（LLM 生成 / dosi 编译）的机制解剖、全部生成路径清单、准确性/速度对比。
> **基线**：2026-10-23，基于本仓代码实读（file:line 均为当日核对）与 docs/ 交叉验证。
> **前置阅读**：[dosi/SQL执行闸门-ClickHouse233兼容.md](dosi/SQL执行闸门-ClickHouse233兼容.md)（执行闸门视角）、[dosi/Dosi建模起步.md](dosi/Dosi建模起步.md)（建模视角）——本文补齐"生成"视角的全景。

---

## 〇、一句话总纲

**SQL 的出生方式只有三种：LLM 写的、dosi 编译的、模板/人给的。** workflow.yml 只是编排层（决定节点顺序），不生产 SQL；dosi 只在 ask_metrics 一系节点里是唯一生产者，在 gen_sql 一系节点里只是可选辅助工具。

---

## 一、主通道 A：LLM 生成（workflow 管道 + agentic 节点）

### 1.1 编排层：workflow.yml 如何生效

- 模式定义：`datus/agent/workflow.yml`，内置四模式：
  - `fixed`：schema_linking → gen_sql → execute_sql → output（经典 RAG 管道）
  - `chat_agentic`：chat → execute_sql → output
  - `gen_sql_agentic`：gen_sql → execute_sql → output
  - `empty`：空
- 模式选择链：`args.workflow` 显式传入（`workflow_runner.py:44`）> `agent.yml` 的 `workflow.plan`（`agent_config.py:1087`，默认 `fixed`）> 兜底 `fixed`；先查 `agent.yml` `workflow:` 段的自定义模式（custom_workflows，可覆盖内置），再查 workflow.yml（`plan.py:210-245`）。
- 节点串里支持别名（`execute`→execute_sql、`chat`→TYPE_CHAT，`plan.py:164-167`）、`parallel:`/`selection:` 嵌套（`plan.py:85-130`）；`ask_metrics` 也是合法管道节点（`plan.py:184-193` 专门构建 AskMetricsNodeInput）。
- **关键边界**：REPL 交互、`datus -p`、web 聊天流（`/chat/stream`）走"单节点 agentic 范式"（`create_interactive_node`），**完全不经过 workflow.yml**；管道范式只由 REPL `/run`、API `run_workflow`（`api/service.py:154`）、benchmark 跑批（`agent.py:181`）触发。

### 1.2 节点解剖

**schema_linking**（仅 fixed 模式）：知识库检索定位相关表，输出表结构+样例到上下文（docs/workflow/nodes.zh.md）。检索底料是 `schema_metadata.lance`（bootstrap-kb 产出）与语义对象投影 `search_semantic_objects`——见 [dosi/知识资产与检索.md](dosi/知识资产与检索.md)。

**gen_sql（GenSQLAgenticNode）**——管道里 SQL 的主要出生地：
- 上下文：`sql_contexts / table_schemas / metrics` 三容器 + 函数工具 `search_metrics`（指标检索）、`parse_temporal_expressions`（时间表达解析）、`search_document`（平台文档）。
- **默认工具面（gen_sql_agentic_node.py:247）**：`"db_tools.*, semantic_tools.*, context_search_tools.*"` —— **dosi 的 query_metrics/get_metric/list_metrics 都在工具面里，但是可选辅助**：LLM 可以先查指标口径再写 SQL，也可以完全无视。根 SQL 永远是 LLM 手写、`db_tools.execute_sql` 执行。
- 策略并行：可配 `strategy="conservative"/"aggressive"/"metric_based"` 多路并行 + SelectionNode 选优（docs/workflow/nodes.zh.md L185-195）。

**fix（FixNode）**：SQL 修复节点，LLM（`autofix_sql`）重写失败 SQL，不执行，产物写回 SQLContext 由后续 execute_sql 跑（`fix_node.py:43,65`）——与 gen_sql 同类。

**execute_sql（ExecuteSQLNode）**：统一执行口，不生成 SQL。取上游 `workflow.get_last_sqlcontext().sql_query` 剥 markdown 后经 DBFuncTool 执行（`execute_sql_node.py:27-32,85-106`）。

**执行底座**：`DBFuncTool.execute_sql`（`tools/func_tool/database.py:2429`）按语句类型分派 SELECT→`read_query`(:2555)、DML→`execute_write`(:2983)、DDL→`execute_ddl`(:2884)；**接受 `.sql` 文件路径**（:2456-2486）——SQL 文本可以来自工作区文件而非 LLM 直出。

### 1.3 同族的 LLM 节点（工具面差异决定"离 dosi 多远"）

| 节点 | SQL 生产 | dosi 可用? | 备注 |
|---|---|---|---|
| gen_sql（管道/子代理） | LLM | ✔ 可选（semantic_tools.*） | 口径无机制保证 |
| chat | LLM | ✘（不建 SemanticTools，`chat_agentic_node.py:560` 仅 getattr 兜底） | 纯自由 SQL |
| explore | LLM | ✘ | 只读（`read_only=True`，写被 `_refuse_write_if_read_only` 硬拒，database.py:311） |
| compare / ask_report / ask_dashboard | LLM | ✔（ask_* 系只读 + 可调模板） | ask_report/ask_dashboard 默认工具面含 semantic_tools.* + reference_template_tools.*（`agent_service.py:184-221`） |
| gen_visual_dashboard / gen_visual_report | LLM | ✔ 可选（`DEFAULT_TOOLS="semantic_tools.*, db_tools.*, context_search_tools.*"`，base_visual_artifact_agentic_node.py:108） | 混合态 |
| gen_table / gen_skill / gen_job | LLM（含 DDL） | ✘ | gen_job 另有 `transfer_query_result` 独立写路径（源库读+目标库 TRUNCATE/INSERT，database.py:3271-3340） |
| 自定义子代理（SubAgentConfig） | LLM | 可配 | bootstrap_bi_subagents.py:271 内置 BI 子代理即带 execute_sql |
| validation llm_runner | LLM（校验用） | ✘ | 父 DBFuncTool 浅拷贝成只读副本（validation/llm_runner.py:292-297） |

---

## 二、主通道 B：dosi 编译（ask_metrics 一系）

### 2.1 三角色与编译机制

docs/knowledge_base/metrics.zh.md 的三角色定义：**OSI YAML 是定义；metrics KB store 是检索投影；Dosi 负责执行**——`query_metrics` 把指标名/维度/时间范围/过滤/排序交给引擎，由引擎编译并运行。

引擎侧（`datus/tools/semantic_tools/dosi/runtime.py`）：
- `engine.compile`（:411 供 dry_run 用）：查询意图 → SQL 文本，**不碰数据库**；编译期把关：指标存在性、JOIN 路径合法性（关系只能多→一）、`fan_out_risk` 扇出保护（绝不悄悄发出会重复计数的查询）、window 指标时间轴约束。表达式按单个标量表达式解析，用户文本不进字符串拼接（注入防线，Dosi建模起步.md L187）。
- `engine.execute`（:435，dry_run=false）：编译+执行一体，SQL 只在 native 引擎（`_native.abi3.so`）内部存在。
- `engine.attribute`（:490-495，归因）：黑盒内编译并执行**多条** SQL（基线聚合/当期聚合/分维度对比），Python 层只见请求进结果出。

### 2.2 两层 query_metrics 与 SQL 可见性

- 外层 `SemanticTools.query_metrics`（func_tool，`semantic_tools.py:1238`）是 LLM 唯一能调到的；内层 `DosiRuntime.query_metrics`（`runtime.py:371`）返回的 `metadata.sql` **在外层被剥**：非 dry_run 走 `_drop_compiled_sql`（`semantic_tools.py:638`，调用点 :1412）→ LLM 工具输出/SSE/action history/chat history 全部无 SQL；dry_run 保留（SQL 即返回体，runtime.py:383-404）。
- 成功执行不落日志；失败路径有截断 `sql_preview`（前 ~60 字符 + `sql_chars` 总长，dosi-engine 经 datus logger 输出到 `~/.datus/logs/agent.YYYY-MM-DD.log`）。
- **物理执行 SQL 的唯一完整落地点：ClickHouse 服务端 `system.query_log`**。
- 要拿编译 SQL：① 提问要求 dry_run；② 从会话历史取 query_metrics 入参做确定性复放（编译是纯函数）。

### 2.3 dry_run SQL 的"可执行性"三层结论

| 层 | dry_run 验证? | 说明 |
|---|---|---|
| 编译层（语法/方言/指标语义/维度成员） | ✔ | 到手即语法干净 |
| 方言兼容层 | ✘ | 是 ch233 反代改写**前**的形态，含 `dateTrunc('month',col)` 写法，CH 23.3 直贴会语法错（改写映射见 ch_compat.py:57-66） |
| 物理层（列存在/数据脏） | ✘ | ask_metrics 未接 warehouse_dry_run_provider，dry_run 零 DB 访问；唯一真验过仓库的是 semantic_authoring 节点（编译 SQL 加 `EXPLAIN` 前缀走 `read_query`，semantic_authoring_agentic_node.py:258-267） |

### 2.4 ask_metrics 节点（唯一"dosi 是唯一生产者"的形态）

- 默认工具面（`ask_metrics_agentic_node.py:45-52`）：search_metrics / list_metrics / get_metric / query_metrics / attribution_analyze / list_subject_tree——**无 execute_sql**，未建模口径直接说明限制，不会切去拼 SQL（docs/subagent/ask_metrics.zh.md L89）。
- 约束：维度名必须逐字取自 get_metric 返回（含 dataset 限定），成员校验 `runtime.py:1043-1062`。
- 入口：REPL `/agent ask_metrics`、`datus -p --subagent ask_metrics`、web API 请求体 `"subagent_id": "ask_metrics"`。

---

## 三、其他 SQL 生成/执行路径（完整清单）

按 **SQL 来源** 分五类：

### A. LLM 生成类（执行走 DBFuncTool）
第一章 1.3 表全部 + 报告落盘链：`report_artifact_tools.save_query`（LLM SQL → 只读校验 → guard → `execute_read_enforced`，report_artifact_tools.py:656-713）。

### B. dosi 编译类
- ask_metrics（交互/批跑）
- `metric_artifact_tools.execute_metric_artifact_query`（:103）：dosi 编译（:156-159）→ `execute_read_enforced`（:167）执行——**dosi 出 SQL、DBFuncTool 跑**的混合态；`execute_published_metric_query`（:223）用冻结模型快照重建 DosiRuntime 同路径
- API 指标预览 `POST /api/v1/explorer/subject/metric/preview`（explorer_routes.py:137-152 → explorer_service.py:914-926，只编译不执行）
- semantic_modeling 子代理的 `validate_semantic` + dry_run 验证（建模闭环）
- attribution_analyze（黑盒内多条 SQL）

### C. 模板/文件类（三者之外的第三种出生方式）
- **参考模板**：`execute_reference_template`——Jinja2 渲染已存 reference SQL → `read_query`（reference_template_tools.py:178/240/333）；`search_reference_sql` 提供 few-shot（gen_sql 命中模板直接填参执行，知识资产与检索.md L91）
- **Dashboard 模板**：`POST /api/v1/dashboard/query` → `.sql.j2` + params 渲染（dashboard_service.py:528）→ `execute_read_enforced`（:560-567）；`save_query_template` 试跑同链（dashboard_artifact_tools.py:281-849）
- **内部画像 SQL**：semantic_discovery_tools 的行数/列画像/时间分布/join 基数统计——Python f-string 拼接（:1182-1573），非 LLM 非 dosi
- **调度作业**：`submit_sql_job`/`submit_sparksql_job` 读工作区 `.sql` 文件提交外部 worker 执行（scheduler_tools.py:63/204/270）
- **execute_sql 的 `.sql` 文件参数**（database.py:2456-2486）

### D. 用户/外部直写类
- REPL `sql>` 模式（repl.py:1892,1950）、bash 模式手动 SQL（bash_mode.py:701）
- API `POST /api/v1/cli/sql/execute`（IDE 控制台，cli_routes.py:26-40 → cli_service.py:228，写→`connector.execute`、读→`execute_read_enforced`）
- API `POST /api/v1/tools/{tool_name}`（可直达 execute_sql/query_metrics，tool_routes.py:20-33）
- MCP server 对外暴露 `execute_sql`/`query_metrics`/`execute_reference_template`（mcp_server.py:948-957）
- 进程外客户端（JDBSee 等）——完全在进程内闸门视野之外

### E. 已废弃（勿再引用）
`reflection`/`dynamic`/`metric_to_sql` 工作流、`reasoning`/`reflect`/`search_metrics`/`date_parser`/`doc_search` 节点已删除（release_notes.zh.md L81），迁移到 fixed/gen_sql_agentic + 函数工具。

---

## 四、两条主通道对比结论

| | LLM 生成（gen_sql/chat 系） | dosi 编译（ask_metrics 系） |
|---|---|---|
| SQL 正确性来源 | LLM 能力 + 上下文质量（每跑一次赌一次） | yml 表达式正确性（一次建模，编译确定） |
| 列名/表名错误 | 可能（跨 dataset 混淆实例：Code 47） | 机制上不可能（列名来自 artifact + 维度成员校验） |
| 口径保真（去重/空键/收窄） | 靠 LLM 复述 yml 描述 | 固化在指标表达式（P0 四组基准验证） |
| 覆盖范围 | 无限（明细/临时口径/模型外 join） | 仅已建模指标与维度，覆盖外明确拒绝 |
| 失败形态 | **静默写错**（跑通但口径错，最危险） | 结构化校验报错（跑不通但不骗人） |
| 速度 | 慢：schema 检索 + 秒级 LLM 生成 + 数倍 token + fix 循环 | 快：2-3 次工具调用，编译毫秒级，轻量指标卡片 |
| SQL 可见性 | 全程可见（就是 LLM 的输出文本） | 默认剥离；dry_run/复放可取；物理 SQL 在 query_log |

**选型**：指标覆盖内的问题走 dosi（更准更快）；覆盖外只有 LLM 通道能答。dosi 的准确率上限 = yml 建模质量；LLM 通道准确率 = 模型下限但覆盖无限。

---

## 五、本环境（yunnan0508 / ClickHouse 23.3.15.29）实测注记

1. **Code 62 中文别名乱码（dosi 通道当前 blocker）**：dosi 编译 SQL 内嵌中文别名（`AS 笔数`、`AS 金额_万元`，来自 yml 指标显示名），HTTP 打到 CH 23.3 变 mojibake 语法错；2026-10-23 当天日志 22 条全此因。P0 对数能通是因为当时指标用英文名。走指标问数前必须解决（指标查询名改纯 ASCII，或扩 ch_compat 代理处理编码）。
2. **`toDate('')` 炸弹**：CH 23.3 `toDate('')` 抛 Code 38；yml 日期表达式一律 `toDate(nullIf(col,''))`（详见记忆与 [11-非税日期字段说明.md](non_tax/11-非税日期字段说明.md)）。这类"编译通过、执行爆炸"的问题 dry_run 查不出来。
3. **ch233_compat 反代**（ch_compat.py）：进程内反向代理，剥 URL 参数 `session_timezone`、把 `dateTrunc('<unit>',col)` 改写为 `toStartOfYear/toStartOfQuarter/toStartOfMonth/toMonday/toDate`；dry_run 产物是改写**前**形态，贴 CH 23.3 前需手工套同表改写。
4. **describe_table 逻辑名混淆（良性噪音）**：LLM 把 dataset 逻辑名（funddivide_transfer）/模型名（fne_fund_main）当物理表名 DESCRIBE → Code 60 噪音（database.py:1566）；dosi 通道机制性免疫此类问题。
5. **成功执行的 query_metrics SQL 不落本地日志**：全量物理 SQL 只在 CH 服务端 `system.query_log`（`WHERE user='yunnan0508' AND type='QueryFinish'`）。

---

## 六、与执行闸门文档的关系

[dosi/SQL执行闸门-ClickHouse233兼容.md](dosi/SQL执行闸门-ClickHouse233兼容.md) 的"SQL 出生路径图"（dosi 编译→①引擎内执行 ②dry-run 文本漏出→execute_sql；LLM 生成/修改→execute_sql）是本文第一章/第二章的浓缩版；本文补充了模板/直写两类出生方式与全部节点/API/MCP 入口清单。两文配合使用：本文管"SQL 从哪来"，闸门文管"SQL 怎么落到 CH 23.3"。
