# Dosi 语义建模速查卡（非税收入收缴域 · yunnan0508）

> **定位**：Dosi（Datus 内置语义引擎，OSI YAML）建模的权威速查参考。回答三个问题：**core 字段有哪些、DATUS 扩展 key 有哪些、它们如何被运行时消费**。
>
> - 依据来源：vendored 规范 `datus/tools/semantic_tools/dosi/schema/osi-core-0.2.0.dev0.spec.yaml`（全文通读）、运行时代码 `datus/tools/semantic_tools/dosi/model.py` / `editing.py`、官方文档 `docs/knowledge_base/semantic_model.md` + `metrics.md`、项目标准 `../non_tax/04-非税收入收缴域语义建模与指标标准.md`。
> - 活教材：`subject/semantic_models/yunnan0508/fne_fund_main.yml`（唯一真实生成模型，所有示例实测取自此文件）。
> - 铁律：YAML 是唯一事实源；**禁止手写**，一律走 `semantic_modeling`（校验 + KB 同步自动完成）。

---

## 一、分层架构总览

```
┌─────────────────────────────────────────────────────────┐
│ OSI Core Schema (0.2.0.dev0)                            │
│ 封闭字段集：name / expression / description / ai_context… │
│ ⚠️ 不允许未知字段，直接放自定义 key 会校验失败              │
├─────────────────────────────────────────────────────────┤
│ custom_extensions（OSI 标准预留的厂商扩展槽）              │
│   - vendor_name: string   ← 命名空间门牌号                │
│     data: string          ← 必须是 JSON 字符串            │
├─────────────────────────────────────────────────────────┤
│ DATUS entry（vendor_name == "DATUS" 的那条记录）           │
│ 承载 Datus 特有行为：时间轴/分类路径/窗口/单位/derive/uid    │
└─────────────────────────────────────────────────────────┘
```

**三个概念一句话**：`custom_extensions` 是 OSI 标准给所有厂商预留的扩展槽；`DATUS entry` 是 Datus 在槽里的一条记录；“Datus 特有行为”就是这条记录 `data` JSON 里承载的 key。

**记忆口诀**：**core 管"是什么"（名、表达式、类型、键、关系），DATUS 管"怎么用"（哪条时间轴、什么粒度、怎么 JOIN、归哪类、什么单位、怎么派生窗口）。**

**跨工具可移植性**：不理解 DATUS 的 consumer（Superset/Looker 等）忽略该 entry 仍可读取 core model；Dosi 专门解析 DATUS entry 作为执行提示。

---

## 三、逐对象字段对照表

### 1. semantic_model（顶层，一个文件一个模型）

| OSI core 字段 | 必填 | 说明 | 本项目 |
|---|---|---|---|
| `name` | R | 模型唯一名（=文件名） | ✅ `fne_fund_main` |
| `description` | – | 模型描述 | ✅ "非税收入资金链（缴款→清分→划拨→缴库）：核心骨架…共 7 dataset、9 条实测验证关系" |
| `ai_context` | – | instructions/synonyms/examples | ✅ instructions: 金额指标一律锚定单 dataset（跨边求和 M:N 膨胀）；生产化时按 §七 复验升级 |
| `datasets` | R | 数据集列表 | ✅ 7 个 |
| `relationships` | – | 关系列表（**属于模型，不属于单 dataset**） | ✅ 9 条 |
| `metrics` | – | 指标列表 | ✅ 16 个 |
| `custom_extensions` | – | 扩展槽（整体 Optional） | 顶层**暂未挂** DATUS entry（合法；DATUS key 全部下沉在 dataset/field/relationship/metric 级） |

### 2. dataset

| OSI core 字段 | 必填 | 说明 | 本项目实例 |
|---|---|---|---|
| `name` | R | 数据集名 | ✅ `paybook_full_high` |
| `source` | R | 物理表全名 **或** SQL 查询 | ✅ `yunnan0508.fne_paybook_full_high` |
| `primary_key` | – | 主键（仅实测验证过的键） | |
| `unique_keys` | – | 唯一键（复合键数组） | ✅ 部分表声明 |
| `description` | – | 业务描述（含行数、粒度） | ✅ |
| `ai_context` | – | 口径说明 | ✅ |
| `fields` | – | 字段列表 | ✅ |

**DATUS key（dataset 级）**：

| key | 说明 | 本项目实例 |
|---|---|---|
| `time_dimension` | 本表主时间轴（只选一个） | ✅ `fill_date` / `cleardate` / `msg_date` |
| `source_type` | 标记查询型 dataset | ✅ `{"source_type":"query"}`（`dim_subject`、`treasury_transfer_dedup`） |

### 3. field

| OSI core 字段 | 必填 | 说明 | 本项目实例 |
|---|---|---|---|
| `name` | R | 字段稳定名 | ✅ `fill_date` |
| `expression` | R | 方言**标量**表达式（非聚合） | ✅ `toDate(ffilldate)` |
| `dimension.is_time` | – | 时间角色标记；Date 类默认 true，**String 类必须显式写** | ✅ 三个时间字段 |
| `label` | – | 业务标签 | ✅ `缴款通知书填开日` |
| `description` | – | 描述（含口径坑位） | ✅ |
| `datatype` | – | 逻辑类型 10 值枚举：String/Integer/Decimal/Float/Boolean/Date/Time/DateTime/DateTimeTz/Opaque | ✅ `Date`/`Decimal` |
| `ai_context` | – | synonyms 等 | ✅ `fsubname` |

**DATUS key（field 级）**：

| key | 说明 | 本项目实例 |
|---|---|---|
| `time_granularity` | 源数据粒度（day/week/month/quarter/year） | ✅ `{"time_granularity":"day"}` |
| `is_dimension` | 能否作分组维度（false = 仅表达式引用/键字段） | ✅ `fid`/`fpid`/`fsublevel` 均 false |

### 4. relationship

| OSI core 字段 | 必填 | 说明 | 本项目实例 |
|---|---|---|---|
| `name` | R | 关系名 | ✅ `funddivide_to_paybook` |
| `from` | R | **多方** dataset | ✅ `funddivide_transfer` |
| `to` | R | **一方** dataset（to_columns 须已验证） | ✅ `paybook_full_high` |
| `from_columns` | R | 外键列（复合键两侧同序全列） | ✅ `[fpaybooksubid]` |
| `to_columns` | R | 键列（与 from 同序同数） | ✅ `[fid]` |
| `ai_context` | – | 何时/为何 JOIN（记录实测验证行数） | ✅ |

**DATUS key（relationship 级）**：

| key | 说明 | 本项目实例 |
|---|---|---|
| `join_type` | `left` 或 `inner` | ✅ 9 条全部 `{"join_type":"left"}` |

### 5. metric

| OSI core 字段 | 必填 | 说明 | 本项目实例 |
|---|---|---|---|
| `name` | R | datasource 内唯一（本项目中文命名） | ✅ `非税缴款金额_直缴` |
| `expression` | R | **纯聚合**，字段带 dataset 限定 | ✅ `SUM(paybook_full_high.famt)` |
| `description` | – | 业务描述 | ✅ |
| `datatype` | – | 逻辑类型 | |
| `ai_context` | – | 口径规则（去重/空键过滤/分口径） | ✅ |

**DATUS key（metric 级，本项目 16 个指标在用 8 种）**：

| key | 说明 | 本项目实例 |
|---|---|---|
| `dataset` | 聚合归属表（`COUNT(*)` 类**必须**显式给） | ✅ `"paybook_full_high"` |
| `time_dimension` | 指标锚定的时间轴（**带 dataset 限定**防冲突） | ✅ `"paybook_full_high.fill_date"` |
| `subject_path` | 三级检索分类（纯检索，不影响计算） | ✅ `["非税收入","资金链","缴款"]` |
| `unit` | 单位（元/笔/个） | ✅ 全部在用 |
| `format` | 展示格式 | 文档提及，暂未用 |
| `fill_nulls_with` | 缺失桶填充 | 引擎契约支持，暂未用 |
| `window` | 窗口行为 `{base, offset:{count,granularity,direction}, calculation}` | ✅ 6 个同比环比 |
| `derive` | 派生机制（type: filter/compose） | ✅ filter×2 + compose×1 |
| `uid` | 稳定身份（24 位 CUID2，**引擎写入永不手改**） | ✅ 每个指标都有 |

### 共享词表（全模型通用）

| 词表 | 值域 | 本项目约定 |
|---|---|---|
| `dialects` 枚举 | ANSI_SQL/SNOWFLAKE/MDX/TABLEAU/DATABRICKS/MAQL/BIGQUERY/SIGMA/THOUGHTSPOT | 只用 `CLICKHOUSE` |
| `datatypes` 枚举 | String/Integer/Decimal/Float/Boolean/Date/Time/DateTime/DateTimeTz/Opaque | Date、Decimal、Integer、String |

---

## 四、四个 Datus 特有行为详解（含真实定义）

### ① 时间轴（time_dimension / time_granularity）

三层结构（每层真实原文出处：field L55/L215/L387，dataset L160/L320/L456）：

```yaml
# 第 1 层 field 级：时间字段 + 源粒度
- name: fill_date
  expression:
    dialects:
    - dialect: CLICKHOUSE
      expression: toDate(ffilldate)      # 本库日期多为 String，必须转换
  dimension:
    is_time: true                        # OSI core
  datatype: Date
  custom_extensions:
  - vendor_name: DATUS
    data: '{"v":"1.11","time_granularity":"day"}'   # Datus 扩展

# 第 2 层 dataset 级：本表主时间轴
    custom_extensions:
    - vendor_name: DATUS
      data: '{"v":"1.11","time_dimension":"fill_date"}'

# 第 3 层 metric 级：指标锚定（带 dataset 限定）
      data: '{"v":"1.11","time_dimension":"paybook_full_high.fill_date", ...}'
```

本项目三条主时间轴：

| 环节 | dataset | 物理表 | 原始列(String) | 逻辑字段 | 实测样本 |
|---|---|---|---|---|---|
| 缴款/清分 | `paybook_full_high` | fne_paybook_full_high | `ffilldate` | `fill_date=toDate(ffilldate)` | '2026-07-23'→2026-07-23 |
| 划拨 | `funddivide_transfer` | fne_funddivide_transfer | `fcleardate` | `cleardate=toDate(fcleardate)` | '2022-12-05'→2022-12-05 |
| 缴库 | `treasury_transfer_dedup`(query) | fne_treasury_transfer_new 去重 | `fmsgdate` | `msg_date=toDate(fmsgdate)` | '2023-05-30'→2023-05-30 |

**要点**：`fill_date` 同时服务缴款与清分口径（同表宽表，清分锚定同一张缴款书）；划拨表主轴用 `cleardate`（未划拨批次 `ftransdate` 稀疏）；窗口指标硬性要求主时间轴是日期类型（`toDate` 转换），字符串无法做时间偏移。

编译后的 SQL 形态（`query_metrics` 按月查询，左闭右开）：

```sql
SELECT
    toStartOfMonth(toDate(ffilldate)) AS metric_time__month,
    SUM(famt) AS `非税缴款金额_直缴`        -- ⚠️ 中文别名必须反引号
FROM yunnan0508.fne_paybook_full_high
WHERE toDate(ffilldate) >= toDate('2025-08-01')
  AND toDate(ffilldate) <  toDate('2025-09-01')
GROUP BY metric_time__month
```

> **ClickHouse 23.3 语法坑**：中文裸标识符（列别名）会报 SYNTAX_ERROR Unrecognized token——多字节字符首字节即断裂。中文别名必须反引号包裹；`--` 注释含中文无碍。

### ② 分类路径（subject_path）

三级数组，纯检索元数据，不影响计算。本项目约定：`["非税收入", "资金链"/"票据链"/"统计核对", 业务词]`。
挪动 subject_path 只改分类不改身份（身份由 `uid` 决定），同一 datasource 指标名必须唯一。

### ③ 窗口（window）

core expression 仍是纯聚合（fallback），比较逻辑写入 DATUS `window` object：

```yaml
- name: 非税缴款金额_直缴_同比
  expression:
    dialects:
    - dialect: CLICKHOUSE
      expression: SUM(paybook_full_high.famt)      # fallback 纯聚合
  custom_extensions:
  - vendor_name: DATUS
    data: '{"v":"1.11","dataset":"paybook_full_high",
            "time_dimension":"paybook_full_high.fill_date",
            "subject_path":["非税收入","资金链","缴款"],"unit":"元",
            "window":{"base":"非税缴款金额_直缴",
                      "offset":{"count":1,"granularity":"year","direction":"back"},
                      "calculation":"value"},
            "uid":"vmke8ep5ak3p56rke8246tie"}'
```

规则：查询粒度（month/quarter/year）是**运行时参数**；缺失比较桶保留 null 不补 0；window 结构由 `semantic_modeling` 按已装引擎契约生成，**不手写**；Dosi 校验 fallback 与 window 语义一致性。

### ④ 单位（unit）

纯展示元数据：`元`（金额）/ `笔`（fid 去重）/ `个`（批次去重）。不改计算，供展示与 AI 理解。

---

## 五、完整 metric 双世界标注（L869-875 真实原文）

```yaml
- name: 非税缴款金额_直缴                     # ┐
  description: 直缴非税缴款金额（…famt 直 SUM） │ OSI CORE
  expression:                                # │（校验严格，字段封闭）
    dialects:                                # │
    - dialect: CLICKHOUSE                    # │
      expression: SUM(paybook_full_high.famt)# ┘  字段带 dataset 限定
  ai_context:                                # ┐
    instructions: 用 fill_date 作业务时间轴；…  │ AI 语境（core 字段）
                                               # ┘
  custom_extensions:                         # ┐
  - vendor_name: DATUS                       # │ DATUS EXTENSION
    data: '{"v":"1.11",                      # │（JSON 字符串）
            "dataset":"paybook_full_high",
            "time_dimension":"paybook_full_high.fill_date",
            "subject_path":["非税收入","资金链","缴款"],
            "unit":"元",
            "uid":"pdaqokomvznqk2anu4rfdemm"}'# ┘
```

**运行时消费方**：

| 消费方 | 读什么 | 干什么 |
|---|---|---|
| Dosi 编译器 | time_dimension、time_granularity、join_type、window、derive、fill_nulls_with | 生成 SQL：时间过滤/上卷、JOIN 类型、窗口展开 |
| KB 投影 | subject_path、unit、format、uid | 建检索索引；ask_metrics 按 subject_path 找指标 |
| 宿主 | uid | 稳定身份，更新/重命名保持不变 |

---

## 六、易混点辨析（源码/实测确认）

1. **`dimension.is_time`（core）≠ `is_dimension`（DATUS）**：前者是时间角色标记；后者是"能否作分组维度"。`fid` 标 `is_dimension:false`（去重键非分析维度）；`fill_date` 是 core 时间字段 + DATUS `time_granularity`。
2. **`is_time` 默认规则**：datatype 为 Date/Time/DateTime/DateTimeTz 时默认 true，否则 false——本库 String 日期列必须显式写 `is_time: true` 并先 `toDate` 转换。
3. **`custom_extensions` 本身是 core 字段**：core 定义"槽"的形状（vendor_name + data:string），DATUS 定义"槽里放什么"。
4. **`time_dimension` 在 dataset 与 metric 上含义递进**：dataset 上是"本表主时间"，metric 上是"指标用哪条时间"（值带 dataset 限定）。

---

## 七、本项目红线（04 号标准 §四~§九）

| # | 禁止 | 正确做法 |
|---|---|---|
| 1 | 手写 semantic_models/metrics YAML | 一律经 `semantic_modeling`（本文档 YAML 仅为形态参考） |
| 2 | 声明未实测验证的键（unique_keys/relationships/primary_key） | 只认 DDL 实测；无键则省略并在 ai_context 注明 |
| 3 | metric 顶层放 dataset/time_dimension/subject_path/unit/window | 全部放 DATUS entry 的 JSON data |
| 4 | 一个对象挂多条 DATUS entry；手改 `"v"` 版本号 | 最多一条；v 由引擎写入 |
| 5 | 跨链用 `fpid` 连票据与缴款（唯一连通键是 `fpaycode`）；`fid` 跨 `_new`/`_high` 混连 | 未验证边只写 ai_context 提示 |
| 6 | 汇缴（une_）与直缴（fne_）混算；未过滤空键 | 分口径；`fcollectid != ''` |
| 7 | 为 0 行表建 dataset | 先查行数 |
| 8 | 跨 dataset 金额 compose / 跨边求和 | 金额指标锚定单 dataset；跨环节对比用双指标并查或 query-backed 对比宽表 |

**口径规则（写死在 expression / ai_context）**：笔数一律 `uniqExact(fid)`；时间兜底 `coalesce(toDate(fmsgdate), toDate(ftransdate))`；缴库直接 SUM 虚增 44 倍（505 行原始含 462 冗余，去重 76 行）。

**对账硬数字（对不上即拒绝上线）**：清分金额 16,016,079,467.68；直缴 fid 去重 1,101；缴款金额 18,332,207,203.13；缴库金额（去重）29,535,106.14；汇缴 9,012 / 票据 53,386。

---

## 八、运行时链路全景

```
用户问"2025年8月各州市清分金额"
  → ask_metrics 按指标 description/subject_path 命中"清分金额"
  → 读 metric DATUS entry: time_dimension=paybook_full_high.fill_date, dataset=paybook_full_high
  → Dosi 编译：时间轴过滤(toDate(ffilldate) 范围) + 粒度上卷 + JOIN(join_type)
  → query_metrics 执行 → 结果带 unit="元"
```

验证路径：`query_metrics(dry_run=true)` 看编译 SQL；`ask_metrics` 问数冒烟；对账基准数字核对。
