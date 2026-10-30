---
name: datus-semantic-modeling
description: datus 语义层（dosi OSI）建模唯一自包含规范：建模判定、模型结构、键与关系、命名声明、dataset/metric 定义标准、DATUS 扩展与 uid、指标能力选择、口径文本纪律、粒度去重、校验对账、禁止事项、施工流程。触发：新建或修改 subject/semantic_models/**.yml、字段/数据集/指标建否判定、问数复测对账、bootstrap-kb 重建、口径变更。做建模一律以本文件为全部依据。
---

# datus 语义建模规范

以 OSI core YAML 编写 datus 语义模型。本文自包含全部依据——建模判定、编写契约、域内标准、口径纪律与施工流程——做建模一律以本文为准。

## 一、建模判定

**建模依据五要素，缺一不建模**：

1. **业务依据**：业务概念、场景边界、口径提示 → 落 dataset/metric 的 description 与 ai_context
2. **物理依据**：选哪张表（宽表优先）、行数、时间范围 → 落 dataset 的 source
3. **键依据**：粒度、关联键实测验证结果 → 落 unique_keys 与 relationships，未验证一律不声明
4. **口径依据**：对账基准数、去重规则、空键过滤、日期兜底 → 落 metric expression 与 ai_context.instructions
5. **分类依据**：三级检索分类 → 落 metric 的 subject_path

**新字段入模走五步判定**：

```text
第 1 步 实测   DISTINCT 码值 + 填充率 + distinct 数——未经实测的列禁止入模
第 2 步 定性   分析口径还是过程记录？流水号/报文/审计元数据/多版本冗余/扩展槽 → ❌ 终止
第 3 步 可解   码值能否赋业务语义？有值无义 → ⏸ 缓建，先问业务
第 4 步 独源   已被覆盖？编码让位名称、副本让位权威底表、可推导 → ❌/⏸
第 5 步 定级   P0 顶级分析维度 / P1 跨链桥键与场景定义 / P2 二级时间轴与低频钻取
```

**永不建模白名单**：事实流水号（非分组键号段）、报文/凭证参数、账号与隐私（acct/idcode/tel/email/证件/联系人）、系统审计元数据（oper/createtime/updatetime/version）、多版本 `_last`、扩展槽 fcustomN、实测死列（distinct ≤ 1 或全空全同值）、已证不连通键（实测 JOIN 0 行的假关联）。数据空缺场景（填充率 < 5% 且对应业务本身缺数据）不建模，由 ai_context 声明"数据空缺"。

**缓建五条**（满足任一即缓建，并记录解锁条件）：码值无字典；同义冗余（解锁：出现按编码精确对齐外部系统的需求）；可推导（解锁：推导性能或正确性出问题）；低频场景暂无问数需求；子流程状态无消费方。

**优先建模信号**：校验型字段（维度侧字段反查事实侧质量，仍先过实测）；实测验证的跨链桥键（下游 join 依赖提前铺）；dataset 缺主时间轴（结构性缺陷，最高优先）；问数失败复盘涉及的列自动进入下批候选。

## 二、模型与文件结构

- 每文件一个 `semantic_model`，一个文件 = 一个主题域，命名稳定 `snake_case`；upsert 整体替换同名对象，保留无关内容
- YAML 是唯一事实源，KB 投影由它派生，不可手工维护投影
- 文件切分：有实测验证边相连的连通组**必须同文件**（join 编译单元 = 文件）；无验证边的孤立表按主题自由成文件；跨环节对比用 query-backed 对比宽表（source_query 预聚合到统一粒度）；跨链对比永远 raw SQL，不建模硬凑
- 文件内分层：**核心骨架**（实测验证边相连，边必须声明）；**同主题补充**（无验证边的小表搭车同文件，不声明 relationship）；**查询型维度** `dim_` 前缀（source_query 去重版维度，仅当宽表内联字段不够用时启用，边需验证 to 侧唯一后声明）
- dataset 绑定限定名物理表（库.表）或一段完整、可复用的 SELECT；被引用的每个物理列都声明为字段
- 选型排除：已被验证超集覆盖的表、0 行空表、合计极小且几乎全空的分表，不建 dataset

## 三、键、粒度与关系

- 键声明照录源 DDL：物理主键入 `primary_key`，声明的唯一约束或整表唯一索引入 `unique_keys`，复合键完整保留声明列序；部分索引与表达式索引不能在其列名上确立整表键；ClickHouse 的 `PRIMARY KEY`/`ORDER BY`、StarRocks/Doris 的 `DUPLICATE KEY` 是排序键，不是唯一性声明
- **键是否真实成立以实测为最终裁决**：粒度判定不能停在"这列叫 fid/fpid"，必须实测该列与明细表、主表的双向命中；字段存在性一律查 `system.columns`（`describe_table` 可能返回幽灵列）；同名键跨链语义漂移（fid≈行键、fpid≈单据键）时，计数口径跟着键走（张数 = 单据键，行数 = 行键），实测结论登记施工台账
- 只有实测验证过唯一的键才写 primary_key/unique_keys；生命周期多版本造成的重复键不声明唯一键，键降为普通字段，去重口径写进 ai_context
- 查询型 dataset 仅当查询可证明保持源键时才保留键声明——一对多 join 会使键重复
- relationship 属于 semantic model，不属于单个 dataset；方向只能**多→一**（from = 事实侧多方）；`from_columns`/`to_columns` 一一配对，复合键两侧同序全列；to 侧必须绑定到目标 dataset 粒度上成立的键，声明前 uniqExact 核验 to 侧唯一性
- 只声明实测验证的连接；假关联（实测扇出、全空列）禁止声明，这类知识放 dataset 的 ai_context 作提示
- to 侧非唯一的边允许声明（行级钻取授权用途），ai_context 写定性非唯一声明——生命周期多版本/明细拆行、跨边求和会膨胀，金额指标一律锚定单 dataset 不做跨边求和；JOIN 命中数与基数快照留施工台账不入 yml（§九）
- 为编译通过而编造键，禁止
- 跨链（票据↔资金）唯一连通键是业务码键（fpaycode）；跨链用单据键 fpid、fid 跨 `_new`/`_high` 混连，禁止

## 四、命名与声明规范

- semantic_model：小写英文+下划线，按业务链命名；dataset：与物理表同名全小写，查询型维度 `dim_` 前缀；field：业务语义 snake_case，物理映射经 expression；metric：中文为主，数据源内唯一；relationship：语义化小写
- subject_path 三级：`["非税收入", "资金链"/"票据链"/"统计核对", 业务词]`
- 所有 expression 用 `dialect: CLICKHOUSE`
- Date 类物理 String 列必须 `toDate(...)` 包裹，空串守卫 `toDate(nullIf(col, ''))`；月表用 `toYYYYMM` 解析或保留 fmonth 并标 `time_granularity: "month"`
- 主时间轴每 dataset 恰一条 = dataset 级 `time_dimension`（时间过滤/指标默认轴的唯一权威）；字段 `is_time: true` 是"可 grain 汇总的时间轴"标记，允许多个——凡可能被询问的非主轴日期（清分日/到账日/入库日/有效期等）保留 is_time，撤掉后该轴按月/按年查询报 `time_grain_required` 且 agent 维度检索不可见；`is_time` ≠ `is_dimension`（`is_dimension: false` = 仅键/表达式引用，不作分组维度）
- 码名分工：`*_code` 管分组过滤、`*_name` 仅展示，成对注册
- 分类码值列 description 必写 码值→含义 与完整值域集合（含空串占位；多值并存写"多值并存，过滤勿假设单值"）；行数/金额/占比快照不入（§九）；同码表跨 dataset 注明"与 XX 同码表"
- 测试样本值与污染比例不入 yml（§九）；数据质量疑点以断供注记表达，只定性

## 五、Dataset 定义标准

```yaml
datasets:
  - name: paybook_full_high
    source: yunnan0508.fne_paybook_full_high    # 限定库.表；查询型 dataset 才用 source_query
    description: 缴款书全生命周期宽表（明细行粒度）
    ai_context: 分析缴款/清分/归属用；金额直 SUM 的前提与去重口径写这里
    fields:
      - name: pay_date
        expression:
          dialects:
            - dialect: CLICKHOUSE
              expression: toDate(nullIf(fpaydate, ''))
        dimension:
          is_time: true
        description: 缴款书缴款日（主时间轴）
        custom_extensions:
          - vendor_name: DATUS
            data: '{"v":"<引擎写入>","time_granularity":"day"}'
    custom_extensions:
      - vendor_name: DATUS
        data: '{"v":"<引擎写入>","time_dimension":"paybook_full_high.pay_date"}'
```

- description 写清粒度；dataset 粒度或预期用途无法从 description 直接看出时写 `ai_context.instructions`；用户会按列名之外的叫法提问时给字段配 `ai_context.synonyms`；其余情况两者都省略——复述 description 只会稀释可执行信息
- 列名不是读者会用的叫法时，给字段起 `label`
- source_query 仅用于结果本身是稳定业务数据集的场景（去重视图、预聚合对比宽表）；升粒度数据集必须自包含、池建全量不预收窄（见 §十）

## 六、DATUS 扩展机制与指标身份（uid）

- OSI core 是封闭字段集，不允许未知字段；Dosi 专有元数据放 `custom_extensions`（vendor_name + data），DATUS entry 的 `data` 编码为**单个 JSON 对象字符串**并盖运行时版本戳
- 引擎按 `vendor_name == "DATUS"` 精确过滤：省略或拼错**不报错**，time_dimension/window/subject_path/unit 全部静默丢失——模型看似完好但行为退化
- 一个对象最多挂一条 DATUS entry；不改动引擎写入的 `v` 版本；契约之外不发明字段；custom_extensions 整体可省略（无 Datus 行为的对象，如普通金额字段）
- 各层 DATUS key：dataset—`time_dimension`（主时间轴只选一个）/`source_type`；field—`time_granularity`/`is_dimension`；relationship—`join_type`（left/inner）；metric—`dataset`/`time_dimension`（带 dataset 限定）/`subject_path`/`unit`/`window`/`derive`/`uid`/`format`/`fill_nulls_with`；semantic_model 顶层无专属 key
- 契约版本锁定：OSI core 0.2.0.dev0 + DATUS 扩展 1.11；引擎/规范升级时本节契约复核
- **指标 uid 由宿主管理，24 位 CUID2**：更新前先读现定义，提交完整对象时逐字保留——改名也不例外；禁止生成、修改 uid 或把它复制给另一个指标；新指标省略 uid，宿主在 upsert 时自动分配；KB 的 uid 来自此扩展字段，不把 locked_metadata.uid 当身份来源

## 七、指标定义标准

```yaml
metrics:
  - name: 非税缴款金额
    description: 非税缴款金额（缴款通知书明细口径）；全业务类型，直缴=按 fbustype='1' 切片
    ai_context:
      instructions: 用 pay_date 作业务时间；按执收单位/科目/归属区划/业务类型分组；提及"直缴"必须按 fbustype='1' 收窄
    expression:
      dialects:
        - dialect: CLICKHOUSE
          expression: SUM(paybook_full_high.famt)    # 字段必须 dataset 限定
    custom_extensions:
      - vendor_name: DATUS
        data: '{"v":"<引擎写入>","dataset":"paybook_full_high","time_dimension":"paybook_full_high.pay_date","subject_path":["非税收入","资金链","缴款"],"unit":"元"}'
```

- `dataset`/`time_dimension`/`subject_path`/`unit`/`window`/`derive`/`uid` 只放 custom_extensions，不放 metric 顶层
- 每个业务指标必配 description、`ai_context.instructions`、三级 `subject_path`
- 口径规则写死在 expression：笔数类一律 `uniqExact(单据键)`；时间兜底用 `coalesce(toDate(a), toDate(b))`；空键过滤与"汇缴/直缴分口径"写入 ai_context.instructions；聚合无字段可推断（`COUNT(*)` 类）必须显式给 `dataset` 键
- 业务类型口径：缴款/清分类指标定义为**全业务类型口径**，"直缴/汇缴"由 `fbustype='1'/'2'` 切片表达；禁止把全类型 SUM 表述为直缴金额；指标名不携带 `_直缴` 后缀；fbustype 仅存在于其所属 dataset，其他 dataset 指标禁止按业务类型分组
- **表达式硬约束**：顶层仅 `SUM`/`COUNT`/`COUNT(DISTINCT x)`/`AVG`/`MIN`/`MAX`；禁止窗口函数、子查询、嵌套聚合、`SUM(1)`、多列 `COUNT(DISTINCT a,b)`、引用其他指标（派生走 derive 键）；单次聚合内所有列必须同一 dataset（`cross_dataset_aggregate`）
- **复杂口径下沉 dataset 粒度**：去重、半可加、粒度修正不能靠表达式技巧——表达式层被聚合白名单挡死（`NotAnAggregate`，投影 synced 0），唯一出路是建 query 数据集升粒度后用纯聚合表达；CH 层能跑 ≠ 语义层能编译，碰硬闸立即回滚
- 指标表达式与 derive 过滤条件一律使用**声明字段名**（≠物理列名时写声明名，写物理列名编译报 Unknown identifier）

## 八、指标能力选择

- **base 基指标**：一个聚合或算术表达式能完整表达业务含义时优先；持久条件用 `CASE WHEN` 写进聚合内部
- **filter 派生**：业务概念是对某个可复用基指标的收窄；**compose 派生**：仅当结果组合两个及以上可复用指标。先编写并校验所有被引用基指标；不内联基指标计算、不造单输入透传指标
- **window 窗口指标**：同环比、滚动、累计、排名、分布或带框架统计。每个窗口结果独立指标，OSI 表达式保持单个普通聚合，派生逻辑进结构化 `window` 对象（结构由引擎契约生成，不手写）；窗口族按预期计算选择，查询粒度是运行时参数；仅当基聚合、时间轴、计算、排序、分区、框架全部一致才复用；比较桶缺失或必需框架不完整时保留有语义的窗口 null（**缺失 ≠ 0**）；主时间轴必须是日期类型
- **跨 dataset compose 禁令**：跨环节对比（如"在途 = 缴款 − 缴库"）经 M:N 边 join 后 SUM 膨胀——用双指标并查或 query-backed 对比宽表（预聚合统一粒度后单表做差）
- **parameterized 参数化指标**：仅当不同调用方必须向同一可复用定义提供有界运行时业务输入；稳定策略属于指标本身；声明每个参数的类型、默认值、允许取值或边界；先 get_metric 查 params，再 `query_metrics(params={...}, dry_run=True)` 验证，覆盖默认值与有意义的枚举/边界，禁止发明未声明参数名
- 显式 measure 元数据仅当需要稳定的引擎侧 measure 身份且无法从表达式推断；契约不存在的能力按"当前引擎不支持"上报，禁止在 YAML 近似模拟；仅当契约明确允许才在同一载体组合多种能力

## 九、口径文本纪律（description / ai_context）

- **总则：只写当前态**。description/ai_context 只陈述此刻正确口径——按"这个口径第一天就是这样定义"来写；口径变更 = **整体替换旧文本**，禁止增补式叠写
- **禁入清单**（出现即删，一个词都不留）：
  - 轮次号与问题序号：round-XX、qXX、题号、"第 N 问"
  - 拍板痕迹：拍板、拍板日期、已确认、决策记录、复测结论
  - 历史过程说明：口径怎么来的、改过几版、施工经过、曾经答错、复测结果、"当时/此前/曾/原"
  - 历史对照："旧 X 不再 Y"、"现改为 Z"式新旧对比——直接写 Z 本身
  - 作答性结论："当前答 0/答没有/勿为凑数放宽"类由当前数据状态推出的答题指令
  - 防御型描述（负向口径句）："非X口径 / 不是X / 与X无关 / 并非 / 不重复计X / 区别于X / 防止误用X"式排除句
  - 自有施工凭证：etl-* 任务单、E 码、回改单、development_process_record 引用及"经X核对/由X验证"句式；内部标准/规范文档引用（"N 号标准"、"§章节"）；内部编号体系指代（关系编号 R*/D*、任务号、批次号——路径本身已表达关系，编号运行时无解析路径，重排即死文本）；抽取层内部实现细节（"中间表"、装载路径、自有抽取 SQL 文件行号）
  - 待定状态词："待"字头动作项（待X提供/待X确认/待人定/待拍板/待复诊/待升级）及"生产化时X"句式（待升级的无"待"变体）
  - 测试库实时值（统计快照）：行数/distinct 数/填充率/JOIN 命中数/值域计数/数据范围/金额占比/样本取值名单/污染比例/施工日期戳（"YYYY-MM-DD 实测"）——测试库回灌即漂移，生产环境无对应物；结论定性直写（值域集合、结构事实、断供），数字证据留施工台账；"实测"动词本身不入（直写结论）
- **可放清单**：口径定义、判定条件、断供注记（必配可执行断言，如"表达式自包含可直接执行，一律实查"；数据空缺只定性——"近全空，时效类问题无数据支撑，一律实查"，不带精确行数/日期值）、结构性拒绝规则、码值分布（码值→含义＋值域集合，行数/金额/占比快照不入）；对账基准数字、JOIN 基数、污染比例留施工台账
- **禁令写承接方**：某字段的被禁用途写在承接方（新维度/新指标）的文档里，被禁字段自身不出现禁词——禁令写被禁方会反把它推向检索 Top
- **禁自有施工凭证，核对结论直写**：描述只锚生产侧权威工件（源码 文件:行、官方 XML），自有侧凭证与"经X核对"句式不入——运行时检索不到，对方改名即死文本；自有抽取 SQL 的文件行号引用同禁（抽取层内部细节，见禁入清单）。结论陈述句直写，凭证删除
- **源码锚按功能检验，写值溯源不入**：源码/官方 XML 锚只许承载判定依据——枚举/字典语义、状态机、官方过滤与比较边界、口径先例（agent 无法从数据推断且会改变 SQL 写法）。写值溯源类（哪个类写值/写值时机/源侧命名族映射/注释出处）不入：不改变查询决策，与自有施工凭证同类，换生产侧外衣不豁免。锚尾冗余（如"物理 colName"与 expression 重复）顺手删
- **禁待定状态词，未决问题出语义层**：描述只写当前 SQL 已落地的可执行行为。已落地选型→直写现行规则；缺判据→断供注记；未决问题登记施工清单，不进语义层
- **禁防御型描述，边界用"正方点名自己"**：口径由正定义（锚定数据集＋粒度＋收窄）唯一决定，"非X/不是X/与X无关/不重复计X"负句不增加信息，反而把被比较对象的检索词带进本文档造成双向吸引，对方改名后负句即成死文本。近义对象并存的边界各自写在本方正口径里、互不出现对方名：代理银行分组写在 pay_bank_code（"「各代理银行代收金额/排名」类问题的分组维度"），收款银行列只写"收款银行视角分组用本列"。粒度声明已蕴含的语义（"每业务键一行"已蕴含头表值不重复计）不再补负句。唯一例外：同族并存口径的分流句可在 instructions 层点名兄弟指标＋判别词（"执收单位/科目/项目分组用 非税缴款金额（明细行口径）"）——这是路由不是防御；description 层不点名
- **记忆粘性**：口径修正后检查 agent 侧会话记忆的旧口径残留——旧数据快照会盖过新口径

## 十、粒度、可加性与去重纪律

- **数值字段按可加性四分类**：行级可加（明细金额类，值粒度=表粒度）→ 表粒度直 SUM；键级常数回填（头表总额类，一个业务键一份值复制到多行）→ 按下面升粒度模式落地；半可加（存量/余额类）→ 禁跨时间轴求和，取期末；不可加（比率/单价类）→ 分子分母分别聚合后再算
- **表粒度 ≠ 问题粒度必须架桥**：头/批级数值（缴款书头表金额、批次金额）被回填复制到多行后，行级直 SUM 按行数放大
- 判别验"**行数 = 键数**"，不验"值一致"——同一键所有行取值全等是回填证据，不是安全证明
- **键级常数回填列的唯一可行落地——升粒度 query 数据集 + 指标重锚，不写警示描述**：

```yaml
# ① 建"业务键粒度"数据集：GROUP BY 业务键，组内常数 any()、行级可加量 SUM()
#    池建全量不预收窄，收窄留给派生与查询参数；日期列包 toDate(nullIf(col,''))
datasets:
  - name: paybook_head
    source_query: |
      SELECT fpaycode,
             any(ftotalamt) AS total_amt,      -- 书级常数：组内任取一份
             SUM(famt)      AS item_amt,       -- 行级可加量：升粒度求和
             any(toDate(nullIf(fpaydate, ''))) AS pay_date
      FROM yunnan0508.fne_paybook_full_high
      GROUP BY fpaycode
    description: 缴款书粒度（头表口径），自明细行宽表按 fpaycode 升粒度

# ② 指标重锚到键粒度数据集，恢复纯 SUM
- name: 缴款金额_头表
  expression:
    dialects:
      - dialect: CLICKHOUSE
        expression: SUM(paybook_head.total_amt)
```

- **表达式层去重不可用**：`arraySum(arrayMap(... groupArray((键,值)) ...))` 在 CH 23.3 能跑（lambda 内 `coalesce(t.2, toDecimal64(0,6))` 兜 Nullable），但被 dosi 聚合白名单拒收（`NotAnAggregate`，投影 synced 0）；按值去重（SUM DISTINCT）数学上就错——同额单据撞车。两条共同决定升粒度数据集是唯一出路
- **去重由粒度承担，不由表达式承担**："GROUP BY 键 + any(值)"在数学上恰等价于按 (键,值) 元组去重求和——键在分组里，值不会被压并（同额单据按键各成一组、各取各的 any）；(键,值) 元组纪律由此由 GROUP BY 结构自动满足

## 十一、校验、验收与对账

- 变更后必须过 dosi 原生解析/编译校验；投影计数与 YAML 一致；至少一条代表性指标 dry-run 编译出 SQL（`query_metrics` dry_run）
- **对账基准来自独立实现路径**（另写的独立直查或外部 cube 侧）——基准方与指标方同用一套写法 = 同错相抵的假阴性；基准本身先过粒度审视再用于对账；对不上拒上线
- 无记录 ≠ 0；分母 0/空不硬算；空侧报"该期无数据"；无数据环节的指标不捏造，由 ai_context 声明"数据空缺"
- CH 23.3 直查坑（诊断脚本可用，禁进模型表达式）：中文裸列别名 SYNTAX_ERROR，须反引号；`LIMIT 1 BY` 不被引擎查询源解析器支持，等价改写 `ROW_NUMBER() OVER (PARTITION BY ...)`；时间范围编译为左闭右开 `[start, end)`；裸列名必须全模型唯一，字段尽量带 dataset 前缀

## 十二、禁止事项

1. 声明未实测验证的键（primary_key/unique_keys/relationships）；为编译通过编造键
2. 跨链用 fpid 连票据与缴款；fid 跨 `_new`/`_high` 混连
3. metric 顶层放 dataset/time_dimension/subject_path/unit/window（属 DATUS custom_extensions）
4. 一个对象挂多条 DATUS 扩展条目；改动引擎写入的 v 版本
5. 汇缴与直缴混算；未过滤空键（`fcollectid != ''`）计汇缴池
6. 为 0 行表建 dataset
7. 跨 dataset 金额 compose、跨边求和；金额指标不锚单 dataset
8. 将全业务类型 SUM 表述为"直缴金额"
9. 指标表达式绕聚合白名单写复杂口径；按值去重
10. 增补式叠写描述；写入轮次/拍板/历史对照；写入作答性结论；写入测试库实时值与自有施工凭证（§九 禁入清单）
11. 被禁用途写在被禁字段自身文档
12. 手工维护 KB 投影；改 YAML 后不重建投影
13. 物理删除指标/字段（对象只增不删，废弃改名留档）；回滚时还原旧描述文字

## 十三、施工流程与扩充

每轮固定动作，顺序执行：

1. 证据先行：新表接入、对账发现新坑 → 先落证据与判定结论（development_process_record 台账），再动模型
2. 改 YAML——声明字段名、按 §四–§八 逐条过；解析校验（`yaml.safe_load`）
3. 查重与唯一入口：每个业务主题（同一题面应命中的口径）在消费面只允许一个绑定入口，同主题出现在两个视图/两个成员=建模缺陷，处置是收敛成唯一入口，不是加指针共存。新增成员落笔前先搜兄弟视图同主题成员（meta 全量按主题词过一遍），已有入口就扩展它，或先定主再动工；同名/同义/同口径的既有声明（全文件＋来源表，过 §一 第 4 步独源判定），重复即不新增。定主判据：①数据权威（名称列全填＞宽表回填列）；②金额可答性（配不出主题对应度量的一侧答不了这题）；③对数（金额粒度不同不可直比，只比值域与覆盖）。收敛动作：输家撤 view includes（cube 层留原料）——透出面消失即不可绑，错误从偶发变不可能；口径迁移/重锚后必做冗余审计——旧承载 0 引用即删（字段/指标/数据集），被迁移的口径声明从旧承载文档上摘除（声明跟口径走，旧承载只留本粒度正声明）。过渡护栏：定主已定、撤成员未做时，可在输家 ai_context 写重定向指针、拆词防翻车——临时手段非终态；同一主题翻车两次=必须完成收敛
4. 拍板判据落地三验齐：①成员实现——存在可绑定成员，sql/filters 即判据本身（判据只出现在描述/对照文本里=未落）；②术语对照导航——题面词指向该成员；③冒领清扫——grep 全库 title/description 的主题词，"×类问题的指标"字样只许出现在实现它的成员上
5. 重建投影：`datus-agent bootstrap-kb --components semantic_model --kb_update_strategy sync-yaml --datasource clickhouse`——dosi 编译是硬闸，失败即回滚坏的部分重跑；**KB 索引不自动重建**，任何 YAML 手改后必须重放，否则 agent 检索拿旧元数据
6. 复测对账：`datus -p "<题目>"`（WSL venv），结果对独立基准
7. 施工记录（轮次、拍板、基准演变）写 development_process_record，不进 YAML

扩充路径：同一口径被反复问、新表接入、问数失败复盘 → 触发建模；(问题, SQL) 历史批量沉淀走 `bootstrap-kb --success_story <csv> --kb_update_strategy incremental`；画像刷新字段描述走 `refresh-profile`；验证过但不值得建指标的 SQL 存 reference_sql（`gen_sql_summary`）；业务事实/规则存 knowledge（`extract-knowledge`）；会话偏好与项目决定存 memory（`add_memory`）。
