# Dosi 建模指南

> 整理自 Dosi 官方文档（dosi.datus.ai）：连接器配置、首个指标查询教程、语义契约，以及官方 orders 示例模型。
> 适用版本：Dosi 0.1.13（Ossie 规范 0.2.0.dev0 / Datus 扩展 1.11）。

## 目录

- [一、对接数仓：dosi-connections.yaml](#一对接数仓dosi-connectionsyaml)
- [二、建模：model.yaml](#二建模modelyaml)
- [三、建模硬规则（语义契约）](#三建模硬规则语义契约)
- [四、动手闭环（5 条命令）](#四动手闭环5-条命令)
- [五、在 Datus-agent 中建模：semantic_modeling 工作流](#五在-datus-agent-中建模semantic_modeling-工作流)
- [六、两条捷径](#六两条捷径)

---

## 一、对接数仓：dosi-connections.yaml

Dosi 把指标查询编译成目标方言 SQL 后**下推给数仓执行**。连接配置格式与 Datus 的 `agent.yml` 共用词汇表，已有 Datus 环境零转换可用。

### 配置文件示例

```yaml
# dosi-connections.yaml（放在工作目录，或用 DOSI_CONNECTIONS 指定）
datasources:
  local-duck:
    type: duckdb
    uri: duckdb:///warehouse.duckdb     # 不写 uri 就是内存库

  prod-mysql:
    type: mysql
    host: mysql.internal
    port: 3306
    username: dosi
    password: ${MYSQL_PASSWORD}          # 从环境变量取，推荐
    database: analytics

  prod-sr:
    type: starrocks
    host: sr.internal
    port: 9030
    username: dosi
    password: ${SR_PASSWORD}
    database: analytics
    default: true                        # --execute 不带 --connection 时用它（最多一个）
```

### 关键规则

- `type:` 必须用**精确小写拼写**（写 `postgresql` / `pg` 会直接报错，没有别名）：

  | type | 数据源 | type | 数据源 |
  |---|---|---|---|
  | `duckdb` / `sqlite` | 本地库 | `postgres` / `hologres` / `dws` / `gaussdb` | PG 系 |
  | `mysql` / `tidb` | MySQL 系 | `oracle` / `clickhouse` / `trino` | 其他 |
  | `starrocks` / `doris` | 分析型 | `snowflake` / `bigquery` / `databricks` | 云数仓 |

  （`redshift` 也是合法 type，SQL 能编译，但还没有执行器，`--execute` 会报 planned。）

- **文件查找顺序**（取第一个存在的）：
  1. `$DOSI_CONNECTIONS`
  2. `./dosi-connections.yaml`
  3. `./osi-connections.yaml`（旧名，回退）
  4. `~/.config/dosi/connections.yaml`
  5. `~/.config/osi/connections.yaml`（旧名，回退）
  6. `./conf/agent.yml`
  7. `~/.datus/conf/agent.yml`
- **密钥**：任何字符串值都可写 `${VAR}` 或 `${VAR:-fallback}`。值**恰好**是 `${VAR}` 时延迟解析（变量没设不影响加载文件，用到该连接才报错）；值只是**包含** `${VAR}` 时加载即解析。明文密码能用但会 stderr 告警。
- **容错**：某条配置写坏不会拖垮整个文件，错误被记录，只有用到那个名字时才抛出。
- **旧拼写迁移对照**（1.0 之前的老写法会直接报错并给迁移提示）：

  | 已废弃 | 改用 |
  |---|---|
  | `dialect:` | `type:` |
  | `user:` | `username:` |
  | `password_env:` | `password: ${VAR}` |
  | `private_key_passphrase:` | `private_key_file_pwd:` |
  | `path:` | `uri: duckdb:///<path>` |
  | `url:` | `uri:` |
  | 顶层 `connections:` 列表 | 按名字索引的 `datasources:` map |

---

## 二、建模：model.yaml

官方 orders 示例的真实结构（三张表、五种指标），照抄修改即可。

```yaml
version: "0.2.0.dev0"

semantic_model:
  - name: orders_model
    description: Minimal e-commerce model
    datasets:                                  # ── 数据集（表/视图）
      - name: orders
        source: main.orders                    # 物理表，三段式 catalog.schema.table
        primary_key: [order_id]
        fields:                                # ── 字段（维度入口）
          - name: order_date
            expression:
              dialects:
                - dialect: ANSI_SQL
                  expression: order_date       # 字段本身可以是表达式
            dimension:
              is_time: true                    # 声明为时间维度，可按 天/周/月/季/年 分桶
          - name: amount
            expression:
              dialects:
                - dialect: ANSI_SQL
                  expression: amount

    relationships:                             # ── 关系（JOIN 的唯一来源）
      - name: orders_to_customers
        from: orders                           # 多端（事实表）
        to: customers                          # 一端（维度表）
        from_columns: [customer_id]
        to_columns: [customer_id]

    metrics:                                   # ── 指标
      - name: revenue                          # 聚合型：单次聚合
        description: Total order amount
        expression:
          dialects:
            - dialect: ANSI_SQL
              expression: SUM(orders.amount)
      - name: avg_order_value                  # 比率型：聚合/聚合（自动防整数除法）
        expression:
          dialects:
            - dialect: ANSI_SQL
              expression: SUM(orders.amount) / COUNT(orders.order_id)
      - name: total_margin                     # 表达式型：跨表多聚合运算
        expression:
          dialects:
            - dialect: ANSI_SQL
              expression: SUM(orders.amount) - SUM(products.unit_cost)
      - name: revenue_mom_growth               # 同环比：Datus window 扩展
        expression:
          dialects:
            - dialect: ANSI_SQL
              expression: SUM(orders.amount)
        custom_extensions:
          - vendor_name: DATUS
            data: '{"v":"1.2","window":{"type":"pop","offset":"1 month"}}'
```

### 结构速查

| 层 | 键 | 说明 |
|---|---|---|
| 顶层 | `version` | Ossie 规范版本，`dosi info` 可查 |
| 模型 | `semantic_model[]` | 一个文件可含多个模型 |
| 数据集 | `name` / `source` / `primary_key` / `fields` | `source` 含空白字符视为内联查询（编译为派生表）；否则按 `.` 切成最多 catalog.schema.table 三段 |
| 字段 | `name` + `expression.dialects[]` | 每个字段是裸 SQL 标量表达式；`dimension.is_time: true` 声明时间维度 |
| 关系 | `from` → `to` + 列对 | **多→一方向**，JOIN 条件为各列对等值 AND，默认 LEFT JOIN |
| 指标 | `name` + `expression` | kind 不用声明，引擎从 SQL 推断：aggregate / ratio / expression |
| 扩展 | `custom_extensions` | `vendor_name: DATUS` + JSON data，如 window（同环比/滚动/累计）、join_type、fill_nulls_with、time_granularity、lod 等 |

### 指标三种 kind（引擎自动推断）

- **aggregate（聚合型）**：单次聚合调用，如 `SUM(orders.amount)`
- **ratio（比率型）**：两侧都是裸聚合的除法，如 `SUM(a) / COUNT(b)`；自动包成 `CAST(numerator AS DOUBLE) / denominator` 防整数除法
- **expression（表达式型）**：其余一切，每棵聚合子树成为独立度量，外围算术（含 NULLIF、CASE）原样保留。注意 `SUM(a)/NULLIF(SUM(b),0)` 是表达式型，**不会**被二次强转

### Datus window 扩展（窗口指标）常用写法

```json
{"v":"1.2","window":{"type":"cumulative","function":"sum"}}                        // 累计
{"v":"1.2","window":{"type":"rolling","function":"avg","periods":2}}               // 滚动
{"v":"1.2","window":{"type":"pop","offset":"1 month"}}                             // 同环比
{"v":"1.3","window":{"type":"cumulative","function":"sum","reset":"month"}}        // 按月重置累计
{"v":"1.3","window":{"rank":{"function":"rank","partition":{"mode":"time_bucket"}}}} // 时间桶内排名
```

---

## 三、建模硬规则（语义契约）

违反会报结构化错误（稳定 snake_case 错误码，`--format json` 可看完整结构）：

1. **关系只能多→一**（`from`=事实表）。沿路径 JOIN 不会让行数翻倍；路径最长 6 跳；多条路径抵达同一数据集报 `ambiguous_join_path`；自关系与成环不跟进。
2. **指标表达式必须含聚合**，只允许 `SUM` / `COUNT` / `COUNT(DISTINCT x)` / `AVG` / `MIN` / `MAX`。不允许：窗口函数（`window_in_metric`）、子查询、嵌套聚合、`SUM(1)`、多列 `COUNT(DISTINCT a,b)`、引用其他指标（派生指标走 `derive` 扩展键）。
3. **单次聚合内所有列必须同一数据集**（`cross_dataset_aggregate`）；裸列名（不带 `dataset.` 前缀）必须全模型唯一，零个→`unknown_column`，多个→`ambiguous_column`。
4. **时间字段**：显式 `is_time: true`，或类型为 Date/Time/DateTime/DateTimeTz 自动生效（审计时间戳可写 `is_time: false` 排除）。粒度 day/week/month/quarter/year 只能作用于时间字段。`'20260101'`、`202601` 这类字符串/整数日期必须声明 Datus `time` 扩展的存储布局，否则无法解析。
5. **`--where` 限制**：不允许子查询、窗口函数、绑定参数；不允许内联聚合（应声明为指标再按名引用）。
6. **明细查询**（`select`）：只投影行级字段，投影里出现指标名报 `metric_in_detail_query`；`from` 固定结果粒度，其余数据集只沿多→一边抵达。
7. **扇出保护**：SUM/AVG/COUNT 这类对重复敏感的聚合在归属数据集上计算，绝不在已扇出的 JOIN 上算——没有安全基时报 `fan_out_risk`，**引擎绝不悄悄发出会重复计数的查询**。
8. **表达式是注入防线**：表达式片段按单个标量表达式解析，用户文本不会经字符串拼接进入 SQL。

---

## 四、动手闭环（5 条命令）

```bash
export DOSI_EXAMPLES=~/.local/share/dosi/examples

# 1. 校验模型（放 CI 里当关卡）
dosi validate --model my_model.yaml
# ✓ 1 semantic model(s) valid

# 2. 浏览模型暴露的指标 / 维度
dosi list metrics    --model my_model.yaml
dosi list dimensions --model my_model.yaml

# 3. 只编译不执行——预览 SQL，--dialect 随时换方言，模型一字不改
dosi query --model my_model.yaml \
  --metrics revenue --group-by orders.order_date:month \
  --pretty --dialect mysql

# 4. 真跑（走 default 连接，或 --connection prod-sr 指定）
dosi query --model my_model.yaml \
  --metrics revenue --group-by orders.status \
  --execute --connections dosi-connections.yaml

# 5. 加过滤、排序、时间范围
dosi query --metrics revenue --group-by orders.status \
  --where "orders.amount > 50" --execute
```

要点回顾：

- `--group-by` 项写作 `dataset.field` 或唯一裸字段名；时间字段加粒度：`orders.order_date:month`，输出列名 `{field}__{grain}`
- 时间范围是 ISO 日期**左闭右开** `[start, end)`，聚合之前编译成 `field >= DATE start AND field < DATE end`
- 换数仓只换 `--dialect`（编译预览）或 `--connection`（真执行），模型零改动——MySQL 没有 `DATE_TRUNC` 时引擎自动改写成 MySQL 惯用写法
- 比率型指标按真正的比率算（如平均订单金额 = 总营收 ÷ 订单数），不是逐行平均

---

## 五、在 Datus-agent 中建模：semantic_modeling 工作流

> 本节转向 **Datus-agent 内的建模实施**：前三节讲的是 Dosi CLI / 手写 YAML 的通用契约，实际项目（如本项目 fne_fund_main.yml 的建立与两批字段补全）应通过 `semantic_modeling` 子代理完成——它在 Dosi 契约之上补齐了"读库取证 → 编译验证 → 自动同步 KB"的完整闭环。

### 5.1 一次运行的工作流（5 步）

1. **检查已有模型，选定唯一目标文件**（每轮只编辑一个 semantic model）；
2. **读真实 schema 和关系证据**（`describe_table` / 实测查询）——不臆造字段名与码值；
3. **按依赖顺序创建/更新** dataset → field → relationship → metric；
4. **对整个目标文件做 validate_semantic 编译验证**（可加 dry-run 指标查询）；
5. **验证通过后把 YAML 自动同步进 KB**（`sync_osi_to_db`）——所以建模后**不需要手动跑 `bootstrap-kb`**。

**产出三态**：`generated`（建好并已同步）/ `skipped`（无需改动）/ `blocked`（证据不足，会解释缺什么）。

### 5.2 关键设计约束（本项目踩过的点均对应）

| 约束 | 本项目实证 |
|---|---|
| **YAML 是唯一事实源**（source of truth）；KB 投影只是可检索派生物，不能直接改投影——手改 YAML 必须跑 `bootstrap-kb --components semantic_model --kb_update_strategy sync-yaml` 重放 | 2026-10-20 实测：两批建模 finalizer 自动同步后，`search_semantic_objects` / `search_metrics` 立即可见新字段与改名指标 |
| **键声明只认 DDL**：主键/唯一键只从物理约束来，不扫数据猜——无键就省略并解释，宁缺勿错 | `fne_paybook_full_high.fid` 非唯一键（147 个重复 fid）——靠 `ai_context.instructions` 声明"笔数必须 uniqExact(fid)"兜住 |
| **每轮只动一个模型文件** | 本项目按 04 号标准分 fne_fund_main / fne_bill_link / … 逐文件推进，正符合该契约 |
| **方言逐条声明**：每个字段 expression 带 `dialect: CLICKHOUSE` | 中文列别名必须反引号、String 日期必须 `toDate()` 包裹，全部写在 expression 内（非本地约定，是方言契约） |
| **指标带稳定 uid**（24 位 CUID2，引擎管理）：改名时**保留 uid**、新建不同指标才省略 | `_直缴`→全口径改名（非税缴款金额/非税缴款笔数）时保留 uid，身份与历史引用不乱 |

### 5.3 在整个体系里的位置

```text
人工/需求 ──> semantic_modeling（建模）──> B4 YAML（事实源，subject/semantic_models/）
                                              │ 自动同步（sync_osi_to_db）
                                              ▼
                                    A1/A2/A3 KB 投影（LanceDB datus_db/）──> ask_metrics / gen_sql 检索使用
                                              │
                                    Dosi runtime（query_metrics 真正算数，读 YAML）
```

- **与 ask_metrics / gen_sql 的分工**：`semantic_modeling` 定义指标与结构（弹药工厂）；`ask_metrics` 用已有指标答数；`gen_sql` 写一条 SQL（语义层给底座，允许超越已有指标）。
- **与手写 YAML 的分工**（对照第三节契约）：契约本身（硬规则、错误码）不变，semantic_modeling 是契约之上的**自动化实施路径**——普通建模走子代理，CLI 手工校验（第四节）仅用于精调与 CI 关卡。
- **配套项目纪律**：字段入模判定走 [07-建模判断标准](../non_tax/07-建模判断标准.md)，字段台账回填走 [06-当前建模字段清单](../non_tax/06-当前建模字段清单.md)，知识资产全景见 [05-知识资产与检索](../non_tax/05-知识资产与检索.md)。

---

## 六、两条捷径

1. **不用手写 YAML**：装好 Datus-agent 后，`semantic_modeling` 子代理读数据库 schema + 业务描述**自动生成 OSI 格式语义模型**（工作流见第五节），`validate_semantic` 兜底校验。手写只用于精调。
2. **照抄示例**：`~/.local/share/dosi/examples/` 下有四套现成模型：
   - `orders` — 最小，教程用
   - `lod-commerce` — LOD 电商全套路（模型、数据、查询）
   - `tpcds` — CLI 参考用
   - `aviation` — 本体参考（手写模型 + 本体）

### 建议路径

先拿 `orders` 跑通第四节第 1、4 步（对着自己的数仓改 `source:` 和连接配置）→ 真实项目转 `semantic_modeling` 工作流（第五节）建模 → 复杂指标（LOD、窗口）同样交给子代理生成 → 字段判定与台账维护走 07/06 号项目标准。

---

## 附：官方文档入口

| 主题 | 地址 |
|---|---|
| 安装 | https://dosi.datus.ai/zh/install/ |
| 各数仓连接配置 | https://dosi.datus.ai/zh/connectors/ |
| 第一个指标查询教程 | https://dosi.datus.ai/zh/tutorials/first-metric-query/ |
| 语义契约（执行语义规范） | https://dosi.datus.ai/zh/semantics/ |
| Datus 扩展（规范） | https://dosi.datus.ai/zh/datus-extensions/ |
| LOD 建模 | https://dosi.datus.ai/zh/lod/ |
| CLI 参考 | https://dosi.datus.ai/zh/cli/ |
| 在 Claude Code 里用 Dosi | https://dosi.datus.ai/zh/agents/claude-code/ |
