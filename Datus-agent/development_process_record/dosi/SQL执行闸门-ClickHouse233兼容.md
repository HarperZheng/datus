# SQL 执行闸门总结 — ClickHouse 23.3 兼容

> 定位：记录 `yunnan0508`（ClickHouse 23.3.15.29）上 dosi 引擎与连接器两条执行路径的兼容闸门——位置、机制、职责与边界。
> 关联：`dosi_semantic_modeling.md` §执行坑表（session_timezone / dateTrunc 两坑的机制根源）。

## 一、兼容性问题（闸门存在的原因）

| # | 不兼容点 | 报错 | 来源性质 |
|---|---|---|---|
| 1 | `SETTINGS session_timezone='UTC'` | Code 115 UNKNOWN_SETTING | dosi 执行器硬编码追加的 **HTTP 参数**，不是 SQL 文本 |
| 2 | `dateTrunc('MONTH', col)` 大写 unit | Code 36 BAD_ARGUMENTS | 23.3 只认小写；dosi 编译器按新方言生成，LLM 写 SQL 同样会写 |

## 二、SQL 执行路径全景

### 2.1 SQL 的两种出生方式（dosi 引擎的两个核心能力）

**① dosi 编译（`engine.compile`）——把查询意图翻译成 SQL 文本，仅此而已，不碰数据库**

```text
输入：查询意图（MetricQuery 字典）            输出：SQL 文本
{"metrics": ["清分金额"],            ──►   SELECT dateTrunc('MONTH', ...) ...
 "dimensions": [...],                      FROM yunnan0508.fne_paybook_full_high
 "time": 2025年, "grain": "month"}         SETTINGS join_use_nulls = 1
```

翻译时引擎读语义模型 YAML（`fne_fund_main.yml`），顺带做编译期把关：指标存不存在、JOIN 路径合不合法、扇出膨胀（fan_out_risk）、window 指标时间轴约束——2026-10-20 事故中漏出的 SQL 即编译产物。只翻译，SQL 全程在 Python 层手里；dry-run（`query_metrics(dry_run=true)`）就是"只编译给你看，不执行"（`runtime.py:411`）。

**② dosi 归因（`engine.attribute`）——回答"指标为什么变化"：贡献度拆解**

例如"清分金额这个月为什么环比涨了"→ 按维度拆解：执收单位 A 贡献 +500 万、科目 B 贡献 −200 万。

```text
输入：归因请求（指标 + 维度 + 基线时间窗 + 当期时间窗）
内部：引擎在黑盒内编译并执行多条 SQL（基线聚合、当期聚合、分维度对比）
输出：每个维度成员的贡献度
```

中间 SQL 在 `_native.abi3.so` 内生成并执行，Python 层只见请求进、结果出——Python 层没有任何可改写点，只有网络层反代能保它在 CH 23.3 上执行。

| | dosi 编译 | dosi 归因 |
|---|---|---|
| 干什么 | 意图 → SQL 文本 | 变化 → 按维度拆贡献 |
| 碰数据库吗 | ❌ 纯内存翻译 | ✅ 黑盒内自己执行 |
| SQL 可见吗 | ✅ 产物在手 | ❌ 中间过程不可见 |
| 代码位置 | `runtime.py:411`（dry-run 在用） | `runtime.py:479` |
| 兼容覆盖 | 产物无论经引擎还是经 execute_sql 执行，都由反代兜底（文本本身不改写） | 反代 |

### 2.2 执行路径现状

```text
dosi 编译 ──► ① 引擎内执行（query_metrics dry_run=false）──► 反代 ──► CH 23.3
        └──► ② dry-run 产出文本 ──► LLM 拿去 ──► execute_sql ──► 反代 ──► CH 23.3
dosi 归因 ──► ③ 引擎内执行（黑盒内编译+执行）──────────────► 反代 ──► CH 23.3
LLM 生成/修改（gen_sql / fix_sql / chat）────────────────► execute_sql ──► 反代 ──► CH 23.3
```

- **①③ 引擎路径**：引擎连接装配时（`engine.py:302`）host/port 被替换为进程内反代，网络层剥 `session_timezone` + 改写 `dateTrunc` 后到达 CH。
- **execute_sql 路径**（LLM 生成、fix_sql、dry-run 文本被再执行）：连接器构建时（`db_manager.py:498`）同样经 `reroute_entry` 换址进反代——与引擎路径共用同一个反代实例、同一份改写逻辑（全仓只有 ch_compat 一处）。连接器方言为 `clickhouse://`（HTTP 驱动，8123 端口），与引擎同构，可被同一反代承载。
- **进程外客户端**（JDBSee 等）：完全在进程内闸门视野之外。

## 三、闸门现状

现状只有一道闸门：**进程内反代**，覆盖引擎路径与全部连接器路径；进程外客户端无闸门。

### 引擎内执行（dosi 原生闸门）

| 项 | 内容 |
|---|---|
| 主体（**dosi 原生**） | dosi 引擎自有执行器：`engine.execute`（`runtime.py:431`，query_metrics dry_run=false）与 `engine.attribute`（`runtime.py:479`，归因）——编译+执行都在引擎内部完成，SQL 与请求参数由引擎代码直达数据库 |
| 原生机制 | 连接装配走 `_runtime_connections`（`engine.py:262`，agent.yml 数据源词表原样传给引擎）；编译期语义校验（fan_out_risk、跨 dataset 聚合禁令、window 约束等）在 SQL 离开引擎前把关 |
| 原生边界 | ① 执行器硬编码追加 `session_timezone=UTC` HTTP 参数、② 按新版方言生成大写 `dateTrunc`，对 CH 23.3 两处原生不兼容；③ SQL 离开引擎即出 datus 侧视野——`session_timezone` 不经 SQL 文本，只能在网络层处理 |

### 兼容层：进程内反代（**Datus 后加，非 dosi 原生**）

| 项 | 内容 |
|---|---|
| 挂载点 | 两处装配口共用同一决策函数 `reroute_entry`（`ch_compat.py:141`）：① 引擎连接装配（`engine.py:302`）；② 连接器构建（`db_manager.py:498`，db_manager 是全仓唯一的连接器创建口） |
| 机制 | HTTP 反代 daemon 线程（按上游单例）：剥 `session_timezone` 查询参数（`_STRIPPED_PARAMS`）+ 改写 `dateTrunc`（`ch_compat.py:37` 正则，大小写不敏感，覆盖 YEAR/QUARTER/MONTH/WEEK/DAY）——改写逻辑全仓只有这一份 |
| 覆盖面 | 引擎流量（query_metrics 执行、归因）+ 全部连接器流量（execute_sql、fix_sql、gen_sql bootstrap、目录/DDL/采样）——连接器方言 `clickhouse://` 走 HTTP 驱动（8123 端口），与引擎同构 |
| 开关 | 数据源条目 `ch233_compat: true` 显式启用（opt-in，不写 / `off` = 原生路径，§六）；键由 `reroute_entry` 摘除、永不下传引擎与连接器；本地地址直通不改写（`ch_compat.py:120`） |
| 运行证据 | 引擎路径：`CH compat proxy for 172.18.166.126:8123 listening on 127.0.0.1:46733`，修复前 Code 115 连续报错 → 修复后零错误。连接器路径：2026-10-20 事故同型 SQL（大写 `dateTrunc('MONTH',…)`）经反代（127.0.0.1:43627）在 CH 23.3 成功返回月度聚合——同型 SQL 未接入时曾报 Code 36（包装为 500006，`datus_sqlalchemy/connector.py:244`） |

### 无闸门路径（现状缺口）

| 路径 | 说明 |
|---|---|
| 进程外客户端 | JDBSee 等手工执行 SQL，完全在进程内闸门视野之外，只能靠人肉方言纪律 |

## 四、共享内核

- **改写逻辑（全仓唯一一份）**：`ch_compat.py` 反代内部——`_rewrite_body()` 正则匹配 `dateTrunc('<unit>', col)` → `toStartOfYear/toStartOfQuarter/toStartOfMonth/toMonday/toDate`（`ch_compat.py:37`，大小写不敏感），纯字符串进出，幂等；`_STRIPPED_PARAMS` 剥 `session_timezone` 查询参数。
- **统一决策点**：`reroute_entry()`（`ch_compat.py:141`）——引擎装配（`engine.py:302`）与连接器构建（`db_manager.py:498`）两处调用；调用方只换地址，不碰 SQL。
- **唯一开关**：数据源条目 `ch233_compat`（§六）——`true` 启用反代，`off` / 不写走原生；环境变量 `DATUS_CH_COMPAT` 已移除，残留于环境的历史值会被忽略。

## 五、覆盖矩阵

| SQL 来源 | 路径 | 反代覆盖 | 结果 |
|---|---|---|---|
| dosi 编译 → 引擎内执行（query_metrics 执行） | 引擎 → 反代 | ✅ | 安全（已验证） |
| dosi 归因（黑盒内编译+执行） | 引擎 → 反代 | ✅ | 安全 |
| dosi 编译 → dry-run 文本 → LLM → execute_sql | 连接器 → 反代 | ✅ | 安全（事故同型 SQL 复验通过） |
| LLM 自写 SQL → execute_sql / fix_sql | 连接器 → 反代 | ✅ | 安全（同一连接器路径） |
| 任何 SQL → 进程外客户端（JDBSee 等） | 闸门外 | ❌ | 靠人肉方言纪律 |

> 事故存证：2026-10-20，dosi 编译产物经 dry-run 漏出后被 `execute_sql` 执行——当时该路径尚未接入反代，直连 23.3，`dateTrunc('MONTH',…)` 报 Code 36（包装为 500006，`datus_sqlalchemy/connector.py:244`）。同型 SQL 现经反代复验通过（§三 运行证据）。

## 六、反代开关

> **状态：已实施（2026-10-20）。** 本节为现状描述。

### 机制

**唯一开关 = 数据源条目顶层 `ch233_compat` 键，显式 opt-in：不写默认关，写 `true` 才开**；环境变量 `DATUS_CH_COMPAT` 已删除（含 `ensure_ch_compat` 内的检查），不再有第二开关。

```yaml
  services:
    datasources:
      yunnan0508:
        type: clickhouse
        host: 172.18.166.126
        port: 8123
        username: yunnan0508
        password: ***
        database: yunnan0508
        ch233_compat: true   # 写 true（或 on/yes/1）= 反代开；off/false/no/0 或不写 = 走原生路径
```

| 配置 | 效果 |
|---|---|
| `ch233_compat: true`（或 `on` / `yes` / `1`，大小写不敏感） | **该数据源**反代开 |
| `ch233_compat: off`（或 `false` / `no` / `0`，大小写不敏感） | 该数据源走原生路径 |
| **不写该键** | **默认关——走原生路径** |

- **opt-in 的含义**：反代只为明确声明的数据源挂载，新数据源与升级后的数据源天然不经过兼容层。
- **实施时必须给 `yunnan0508` 补 `ch233_compat: true`**——否则反代不再自动挂载，CH 23.3 的两坑（Code 115 / Code 36）立即回归。
- **升级后操作**：把 `true` 改 `off` 或直接删键 → 原生路径，该键即可退役。
- **多数据源**：每个数据源条目独立声明，互不影响。
- **解析零改动**：`ch233_compat` 对 `DbConfig` 是未知键，`filter_kwargs` 自动收进 `extra`，引擎路径（`_extract_db_config` 把 extra 拍平到顶层）与连接器路径（`filtered_config.update(extra)`）都会把它带到条目顶层——无需改任何 YAML 解析。
- **摘键是硬约束**：该键绝不能到达下游——Rust 引擎的 connections 词表不接受未知字段，`ClickHouseConfig` 是 `extra="forbid"` 会直接报错。由 `reroute_entry`（两条路径共用的唯一决策点）统一处理：**先摘键（返回剥离后的条目），再决定换址与否**；调用方零改动。
- **日志**：跳过反代时打一条 INFO 注明原因（未启用 / `off`，host），开启时的反代监听日志维持现状——两种状态一眼可辨。
- **生效时机**：agent.yml 进程启动时加载，改键后**重启 datus 进程**生效。

### 落地记录（2026-10-20，已完成）

1. `reroute_entry`（`ch_compat.py:142`）：opt-in 判定——`true/on/yes/1` 才换址；先取值、再摘键（副本，调用方入参不被改动），键永不下传；跳过时打一条 INFO 注明原因（`ch233_compat not set` / 具体值 + host）。
2. `ensure_ch_compat`：`DATUS_CH_COMPAT` 检查已删除；残留于环境的历史值被忽略（回归测试 `test_stale_compat_env_var_is_ignored` 防止旧 env 静默关掉保护）。
3. `conf/agent.yml`：`yunnan0508` 已补 `ch233_compat: true`，保护不中断。
4. 测试：env 急停用例删除；新增 opt-in 四类（不写=关 / `true` 系=开 / `off` 系=关 / 键被剥离且入参不动）+ 引擎与连接器两侧的换址/未启用用例，124 passed。
5. 端到端复验（真实 agent.yml → `filter_kwargs` → 连接器）：`ch233_compat` 收进 `extra`、连接器换址 `127.0.0.1:38397`、键未泄漏进连接器配置、事故同型 SQL 在 CH 23.3 成功返回。

## 七、退役条件

CH 升级 ≥23.5（原生支持大写 `dateTrunc` 与 `session_timezone`）→ 把 `ch233_compat: true` 改为 `off` 或直接删键（§六），重启 → 回原生路径。
