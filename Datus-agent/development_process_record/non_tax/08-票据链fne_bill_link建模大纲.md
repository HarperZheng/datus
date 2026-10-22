# fne_bill_link 票据链建模大纲（含 2026-10-20 实测勘误）

> **定位**：`fne_bill_link.yml`（票据链 B1-B4）建模前的大纲文档，回答三件事：**实测发现了什么口径问题、datasets/字段/指标怎么摆、实施步骤怎么走**。
> **依据链**：[03-宽表选型清单](03-宽表选型清单.md)（B 场景与键）→ 本文档（实测勘误 + 大纲）→ `subject/semantic_models/yunnan0508/fne_bill_link.yml`（待产）。
> **判定标准**：[07-建模判断标准](07-建模判断标准.md) 五步流程；本文所有码值/键/金额结论均为 **2026-10-20 对 yunnan0508 实测所得**（实测 SQL 见 §七 留档）。
> **状态**：大纲待确认（§八 三个待决问题），确认后由 `semantic_modeling` 子代理落 YAML（04 §2.4 禁止手写）。
> **版本**：v2 补充版（2026-10-20 晚）——按缺口清单复核补入：单位/区划/业务类型/资金性质维度、paybook 状态与单位区划、键字段声明（§三.1）、对账基准（§3.5）、fpaybill*/fconfirm 族实测修正；§一要点 3 的金额证据修正（fbustype=4 为测试票来源）。

---

## 一、实测发现的 4 个口径要点（建模前必须钉死）

| # | 发现 | 证据 | 对建模的影响 |
|---|---|---|---|
| 1 | **cbill_high 自身是多版本冗余表**：1,495 个 fid 各有 2~12 份重复，共 8,524 行冗余，重复行 famt/fstate/fpid 完全一致（纯报文重发） | 53,386 行 ≠ 46,357 distinct fid；raw 金额 1,541,083,489,625.32 vs 按 fid 去重 1,231,407,283,148.44（虚增 25%） | 参照 treasury_transfer_dedup 先例，**cbill_high 做 query-backed 去重**（fupdatetime 最新版 LIMIT 1 BY fid → 46,357 行），禁止裸 count/SUM |
| 2 | **cbill_high.fid 是"行键"而非"票据键"**：fid 与 item 明细 fid 同域（46,351/46,357 命中），fpid 才是票据单据键（=cbill_new.fid，39,277 命中）；item 明细字段已内联进 cbill_high | `item.fpid = cbill_high.fid` **0 行**（03 清单 B1 键在 high 链不成立）；`item.fpid = cbill_high.fpid` 40,261 命中 | **勘误 03 B1**：high 链内不再连 une_cbill_item_new（B1"票据+项目明细"一表全答），开票张数指标口径从 04 §5 的 `uniqExact(fid)` 改为 **`uniqExact(fpid)`** |
| 3 | **famt 是票面应收金额，且测试污染比资金链严重一个量级**：>100 万的 70 张票合计 1,236,410,460,376.66（占 99.99%），单笔最高 1,957.57 亿；大票全部挂在 **fbustype='4'**（4,892 行/2,670 票合计 153.13 万亿，含小票）与 '5'（-444.46 亿负票）下，开票单位为测试单位（云南测试单位0831/通用测试0801/丽江税务局-yshj）；≤100 万区间合计 **-50.03 亿（负票/红字票存在）**；fbustype='1'（主流码 40,025 行/31,185 票）金额 148.95 亿、'3' 区间 -5.97 亿 | 金额 Top15 抽样（fpayername='001'、测试单位名）+ fbustype 分组金额（v2 修正：v1 误判测试票全表分布） | 票面金额指标必须声明"含测试大票与负票，仅供票据域内分析，**禁止与资金链实缴 183 亿混比**"；fbustype/fpayername 建模须声明污染 |
| 4 | **票据↔缴款连通是约三成的子集连通**：cbill 侧 93.1% 票据 fpaycode 为空（去重后 43,145/46,357 张无码）；paybook 侧 fpaycode 100% 非空且=fpid 一一对应；跨表命中 2,380/8,044 码 | cbill 一个码挂多张票（022022032110000001→27 张票；53000023795000002059→25 张票） | 边语义 = **cbill:n → paybook:1**；跨链分析必须声明"无码票据不可达"，不硬凑 |

另：冲红（B8）空缺再次印证——`fwriteoffbillid` 全空（53,386/53,386），但 **`frelatedbillid` 有 7,488 行非空，是本库唯一的票据关联信号**（换开/关联票），纳入本批 P1。

**v2 补充实测（2026-10-20 晚，缺口复核）**：

| # | 发现 | 证据 | 对建模的影响 |
|---|---|---|---|
| 5 | **paybook_high.fstate 是有意义的三态生命周期**：'1'=4,416 单/1.37 亿、'2'=1,260 单/0.51 亿、'3'=3,336 单/**183.35 亿**——state=3 金额与资金链实缴 183.32 亿量级吻合（大概率=已完成/已缴款态） | fstate 分组实测（§七-⑥） | **09 v1 最大遗漏**：paybook 字段表缺状态字段；补 P0 `book_state`，与 cbill 的近常量 fstate（1=51,583/2=1,323）价值完全不同 |
| 6 | **fbustype 真实存在且 8 码**：1=40,025/4=4,892/2=4,366/3=3,509/8=480/5=74/10=35/6=5 行；测试大票集中在 '4'/'5'；'8'=480 行仅 8 个 fpid（与 fstate 空、ffundsnature 空同簇，疑似脏数据簇） | fbustype 分组实测（§七-④） | 09 v1 只勘误了幽灵列 fbusinesstype，未处理真实列 fbustype；补 P0 `bus_type`（同码表=fne 侧，金额侧污染声明） |
| 7 | **ffundsnature 6 码跨域同码表但码域扩张**：4=31,812/12=15,472/11=4,584/2=749/3=226/13=63 行；fne 侧字典（fne_paybook_full_high 实测）仅 12/11/2/5 四码——**码 4（占比 68.7%）在 fne 侧无样本**，码 3/13 超出 04 建模时的已知域 | ffundsnature 分组实测（§七-⑤） | 补 P0 `funds_nature`，description 写"与 fne 侧同码表但域含 4/3/13 扩张码，4 疑似非税通用码待业务"；金额混比红线同样适用 |
| 8 | **03 的 B3=5,830 是原始行级 JOIN 口径**：cbill 原始 53,386 行 × fpaycode JOIN paybook=5,830 行（含 8,524 行报文重发虚增）；按 fid 去重后=3,655 行；码级去重命中=2,380 码 | 行级/去重行级/码级三口径实测（§七-⑦） | 09 v1 的"2,380"未注明口径，与 03 的 5,830 并存易误读；R1 边基数声明统一为**码级 2,380/8,044 + 行级 5,830(原始)/3,655(去重)** |

### 1.1 勘误登记

| 原结论（出处） | 勘误后 |
|---|---|
| 03 清单 B1：`item.fpid = cbill.fid`（99,093 ✅） | 该验证边只对 `_new` 链成立（cbill_new.fid=item.fpid 39,277）；**high 链上 `item.fpid = cbill_high.fid` 实测 0 行**，正确键为 `item.fpid = cbill_high.fpid`（40,261）。B1 在 high 链直接用 cbill_high 内联明细列，不建 item dataset |
| 04 §5：票据开票张数 `uniqExact(cbill_high.fid)` | fid 是明细行键（含 8,524 行报文重发），**张数口径改为 `uniqExact(fpid)`**；明细行数另立指标 `uniqExact(fid)`（去重后） |
| 03 清单 B3/B4 边基数认知 | fpaycode 连通是子集连通：cbill 侧 93.1% 无码；命中 2,380/8,044 码；一个 paybook 码可挂多张票据 |

## 二、dataset 分层（fne_bill_link.yml，按 04 §2.2 + 实测修正）

| 层 | dataset | 粒度/行数 | 说明 |
|---|---|---|---|
| 核心骨架 | `cbill_high` | **query-backed 去重**，46,357 行票据明细行 | 物理表 une_cbill_high（122 物理列），source_query 按 fid 取 fupdatetime 最新版；票据头+项目明细合一（fitemcode/fitemname 内联），**不建 item 表**；主时间轴 `fdate`（去重后 0 空值，2019-08-27~2026-09-09） |
| 核心骨架 | `paybook_high` | 单据粒度 9,012 行 | 汇缴通知书；**R1**：`fpaycode = cbill_high.fpaycode`（2,380 码命中✅，cbill:n→paybook:1，预期基数写入 ai_context）；时间轴 `fdate`（2021-06-10~2026-09-09） |
| 同主题补充（二期） | `fbe_writeoff_billitem` / `ubr_stock` / `fbe_stock_out` / `ube_stock_invalid` / `fab_bill` | 1,146 / 352 / 500 / 39 / 88 | 核销/库存/出库/作废/票据档案；无验证边不声明 relationship |
| 查询型维度 | `dim_agen` | 按需复制 | cbill 侧单位名称已内联（faccagenname/fagenname），出现编码对齐需求再复制 |

> 不建表理由备查：`une_cbill_item_new` 明细字段已内联进 cbill_high 且无独立金额列（仅 fpayableamt 应收分项，合计 92.57 亿）；`une_cbill_new` 与 cbill_high 键域为 fid≡fpid 关系（03 §五.7），不重复建模；`une_writeoff_new` 0 行（B8 空缺）。
>
> **dim_agen 关联性实测**（v2）：cbill_high 去重后 78 个 fagenidcode，其中 59 个可关联 fab_agen 去重维度（命中率 75.6%）——单位层级钻取时 19 个单位不可达，需在 dim_agen 边的 ai_context 声明。

## 三、字段建模清单（v2 重排，逐列过 07 五步）

### 三.1 键字段（v2 新增小节——指标编译依赖，必须声明）

> Dosi 要求"指标表达式引用的物理列必须声明为字段"；§四指标用到 `cbill_high.fpid`、`cbill_high.fid`、`paybook_high.fid`，落 YAML 时缺失即编译失败。v1 曾写"fpid 同义不重复建模"，但那只适用于**跨 dataset 复制**场景，本 dataset 内部键列必须声明（`is_dimension: false`，不进维度检索）。

| dataset | 字段 | 物理列 | 声明要点 |
|---|---|---|---|
| cbill_high | `fid`（行键） | fid | is_dimension:false；description 注明"明细行键，去重源键，指标 uniqExact(fid)/uniqExact(fpid) 依赖" |
| cbill_high | `fpid`（票据键） | fpid | is_dimension:false；description 注明"票据单据键≡cbill_new.fid，开票张数口径" |
| paybook_high | `fid`（单据键） | fid | is_dimension:false；通知书张数口径 |
| paybook_high | `fpid`（桥键同义副本） | fpid | is_dimension:false；不重复建模但需声明以承载 fpaycode 桥语义（fpaycode=fpid 一一对应的实证锚） |

### 三.2 cbill_high（去重后 46,357 行）

| 优先级 | 字段 | 物理列 | 依据 |
|---|---|---|---|
| P0 | `bill_code`/`bill_name` 票种 | fbillcode(31) / fbillname(44) | 名称优先惯例；fbillcode 可与 mon_billtype（11 行票据种类目录）交叉校验 |
| P0 | `bill_state` 票据状态 | fstate：'1'=51,583 / '2'=1,323 / ''=480 行(仅 8 fpid) | 核心切分维度；**码值含义待业务确认**（mon_billtype 实测为票据种类目录，非状态字典），description 写实测分布+待确认标注 |
| P0 | `bus_type` 业务类型（v2 新增） | fbustype：'1'=40,025/4=4,892/2=4,366/3=3,509/8=480/5=74/10=35/6=5 行 | **真实列此前漏建**（v1 只勘误了幽灵列 fbusinesstype）；与 fne 侧同码表（同码域 1-8）；金额侧污染集中在 4/5 码、'8'=480 行与 fstate 空/ffundsnature 空同簇（脏数据簇，仅 8 fpid）；码值含义沿用 fne 侧认知+待业务；同时作为**金额过滤口径**（票面金额大票分布声明锚点） |
| P0 | `funds_nature` 资金性质（v2 新增） | ffundsnature：'4'=31,812/12=15,472/11=4,584/2=749/3=226/13=63 行（另空 480=脏簇） | 与 fne 侧同码表但**码域扩张**：fne 侧实测仅 12/11/2/5 四码，**码 4（占 68.7%）在 fne 侧无样本**（疑非税通用码）、3/13 超出 04 已知域；description 写"与 fne_paybook_full_high.ffundsnaturecode 同码表、扩张码 4/3/13 待业务"，交叉验证点 |
| P0 | `agen_idcode`/`agen_name` 执收单位（v2 新增） | fagenidcode(78) / fagenname(97)；faccagenidcode(79)/faccagenname(107) | "按单位统计开票"最自然问数；名称+编码成对建模（07 §4.1 单位主维度惯例，同 fne 侧 fchgagenidcode+fchgagenname）；与 dim_agen 关联命中 59/78（§二）；**acc 代理侧（faccagen*）缓建**——代理银行/收款单位语义未确认前不双轨，避免单位口径混淆 |
| P0 | `rgn_code`/`rgn_name` 区划（v2 新增） | frgncode(10) / frgnname(9) | 归属区划维度（与 fne 侧 frecrgncode 同角色）；编码 10/名称 9 的 1 差异建模时先 distinct 对齐（可能存在空码非空名行） |
| P0 | `pay_code` 票据关联码 | fpaycode | 跨 dataset 桥键（R1 依赖）；description 声明 93% 空码与"码→多票"扇出 |
| P0 | `bill_amt` 票面金额 | famt | 唯一金额列；ai_context 声明票面≠实缴、测试大票占 99.99%（fbustype 4/5）、含负票（≤100 万区间合计 -50.03 亿） |
| P0 | `bill_date` 开票日期 | toDate(fdate) | 主时间轴 is_time，grain=day |
| P0 | `item_idcode`/`item_name` 收费项目 | fitemidcode(91) / fitemname(185) | 明细行粒度内联，与资金链同码表注明 |
| P1 | `bill_source` 票源 | fbillsource（6 distinct） | 渠道分析候选；建模时补 distinct 分布 |
| P1 | `related_bill_id`/`related_bill_no` 关联票据 | frelatedbillid/no（7,488 行非空） | 本库唯一票据关联信号（B8 冲红空缺下的替代）；票号类字段按 07 §2 属号段，此处按"关联关系键"建模并说明 |
| P1 | `payer_type` 缴款人类型（v2 实测落定） | fpayertype：'1'=46,756/'2'=6,012/''=618 | 实测 2+空值；个人/单位疑似映射待业务确认后补语义，先按 P1 建模写实测分布 |
| ⏸ | `bill_no` 票据号 | fbillno（26,744 distinct，非唯一；与 fpid 1:1.5 映射，换开产生多票同号） | 号段类；解锁条件=票号级追溯需求 |
| ⏸ | 交款账户/银行族、fpbcbillid、fsecuritycode、fcheckcode | — | 隐私/内部码（07 §2） |
| ❌ | `fwriteoffbillid/batchcode/no`（全空）、`fdonatetype`（1 值死列）、fcustom1~N、fauthor/foperator 等审计元数据 | — | 死列/白名单 |

### 三.3 paybook_high（9,012 行；v2 重排，补状态/单位/区划/项目）

| 优先级 | 字段 | 物理列 | 依据 |
|---|---|---|---|
| P0 | `book_state` 通知书状态（v2 新增，**v1 最大遗漏**） | fstate：'1'=4,416/1.37 亿、'3'=3,336/183.35 亿、'2'=1,260/0.51 亿 | 三态生命周期，state=3 金额与资金链实缴 183.32 亿量级吻合（疑=已完成/已缴款态）；比 cbill 侧近常量 fstate 价值高一个量级；码值语义待业务确认，description 写三态实测分布+金额交叉证据 |
| P0 | `agen_idcode`/`agen_name` 执收单位（v2 新增） | fagenidcode(55) / fagenname(72) | 与 cbill 侧同角色同码表；dim_agen 可关联（cbill 侧已验证 75.6%，paybook 侧同法） |
| P0 | `acc_rgn_code`/`acc_rgn_name` 受理区划（v2 新增） | faccrgncode(9) / faccrgnname(13) | paybook 特有受理区划（cbill 侧无 acc 前缀列，system.columns 已复核）；名称 13>编码 9，同码表对齐规则同上 |
| P0 | `belong_rgn_code` 归属区划（v2 新增） | fbelongrgncode(20) | 与 fne 侧 paybook_full_high.fbelongrgncode（已建 belong_rgn）同码表 |
| P0 | `item_idcode`/`item_name` 收费项目（v2 新增） | fitemidcode(66) / fitemname(89) | 通知书明细项目 |
| P0 | `pay_code` | fpaycode（100% 非空=8,044，与 fpid 一一对应） | R1 桥键 |
| P0 | `book_amt`/`book_total_amt` | famt/ftotalamt | 通知书金额 |
| P0 | `book_date` | toDate(fdate) | 主时间轴 |
| P1 | `pay_mode` 缴款方式 | fpaymode：''=6,844 / 11=1,921 / 12=133 / 9=77 / 13=25 / 21=11 / 22=1 | **无字典**→07 §3.1 缓建；空值占 76%+码值无义，待业务确认 |
| P1 | `change_more_bill` | fchangemorebill（3 distinct） | 疑似换开标志，建模时先 distinct+样本核对语义 |
| ❌ | `fisfinal`（1 值死列）、隐私族、fcustom | — | |
| ❌ | `fpaybillid`/`fpaybillbatchcode`/`fpaybillno`（v2 实测修正：**9,012 全空**） | — | v1 曾把这三列列为 ⏸ 待业务，实测为死列，降 ❌ |
| ⏸/❌ | **fconfirm 族（v2 新增判定）**：`fconfirmcode`（99% 空：8,923 空/89 非空）→ ❌ 死列；`fconfirmpaymode`（10 distinct 无字典，空值占比未测）→ ⏸ 待业务；`fconfirmtotalamt`（372 distinct，String 存金额）→ ❌ 不建——金额存 String 本身是数据质量问题（值含 '100'/'100.66'/'1' 等，无法安全 toDate/toDecimal 转换保障精度），确认金额已有 famt/ftotalamt 覆盖（独源原则） | — | 07 §2 系统元数据+§3.1 无字典 |

> **工具勘误**：`describe_table` 曾返回幽灵列（cbill_high 的 fbusinesstype、paybook_high 的 fisinvoice/fisarriveaccount/fisincome/fbillname/fbillsource 实测不存在），本清单已全部按 `system.columns` 实际列复核——建模时字段存在性一律以 `system.columns` 为准（07 §1 实测精神）。注意：幽灵列勘误≠真实列不建——**fbustype 真实存在（8 码），v1 已补为 P0**。

## 四、指标清单（首批 1 个起量 + §八增量池）

| 指标 | 表达式 | subject_path | 说明 |
|---|---|---|---|
| **票据开票张数**（首批起量） | `uniqExact(fpid)` | ["非税收入","票据链","开票"] | **勘误 04 §5**：原 fid 口径会虚增 15%（行≠票）；依赖 §三.1 键字段声明 |
| 开票明细行数（增量） | `uniqExact(fid)` | 票据链/开票 | 明细行口径，与张数成对 |
| 票面开票金额（增量） | `SUM(bill_amt)` | 票据链/开票 | ai_context 硬声明：测试大票+负票，禁与资金链混比 |
| 汇缴通知书张数（增量） | `uniqExact(paybook_high.fid)` | 票据链/通知书 | 依赖 §三.1 键字段声明 |
| 关联票据行数（增量） | `countIf(related_bill_id != '')` | 票据链/关联 | 换开/关联分析 |
| 窗口族（增量） | 开票张数同比/环比 | 票据链/开票 | 时间轴 bill_date，**grain 必须进 group_by**（yunnan0508 已验证规则） |

## 五、口径红线（写入 ai_context.instructions）

1. **去重强制**：cbill_high 经 source_query 按 fid 去重后建模；任何直连物理表的金额/计数口径视为错误；
2. **金额隔离**：bill_amt=票面应收 ≠ 资金链实缴（fne_paybook_full_high.famt）；跨链对比永远 raw SQL 且只比张数不比金额；
3. **连通声明**：fpaycode 空 93%，无码票据在跨链查询中不可达，须显式告知而非静默丢行；
4. **空缺声明**：冲红/核销回写（B8）本库无数据；fstate 码值、fpaymode 码值待业务确认；
5. **污染声明**：fpayername 及金额侧测试污染比例建模时实测后写入（沿用 07 §5 规范）；
6. **单位维度污染提示**（v2）：fagenname 97 名含测试单位（0831/0801 系），按单位统计开票时金额侧不可信、张数侧基本可用；与 dim_agen 关联命中 75.6%（19 单位不可达）须在钻取时提示；
7. **同码表声明**（v2）：bus_type/funds_nature 与 fne 侧同码表但**码域扩张**（fbustype 多出 '10'/'6'，ffundsnature 多出 4/3/13），跨链对齐时以实测码域为准，不做静默截断。

### 3.5 对账基准数字（v2 新增小节——散落正文的核心锚点汇总）

| 基准 | 数字 | 口径 | 出处 |
|---|---|---|---|
| cbill_high 原始行数 | 53,386 | 物理表行数（含 8,524 行报文重发） | §一.1 |
| cbill_high 去重行数 | 46,357 | 按 fid 去重（建模粒度） | §一.1 |
| cbill_high 去重票数 | 40,261 | distinct fpid（开票张数口径） | §一.2 |
| cbill_high 去重金额 | 1,231,407,283,148.44 | 按 fid any(famt) 汇总（**测试污染，仅票据域内用**） | §一.1 |
| 票据↔汇缴 码级命中 | 2,380 码 / 8,044 码 | fpaycode 双侧 distinct 交集 / paybook 侧 | §一.4 |
| 票据↔汇缴 行级命中 | 5,830（原始）/ 3,655（去重） | 原始行级 JOIN（=03 B3 数字）/ 按 fid 去重行 JOIN | §一.8 |
| paybook_high 单据数 | 9,012（8,044 fpid） | 物理行 / distinct fpid（63 行多版本） | §二 |
| paybook state=3 金额 | 18,335,050,390.75 | fstate='3' 分组 SUM——与资金链实缴 183.32 亿吻合 | §一.5 |

## 六、实施步骤（确认大纲后执行）

1. `task(semantic_modeling)`：创建 `subject/semantic_models/yunnan0508/fne_bill_link.yml`，按 §三 v2 清单建 cbill_high（query-backed 去重，含键字段声明）+ paybook_high + R1 边 + 首批指标，Dosi 原生校验；
2. 更新 [06-当前建模字段清单](06-当前建模字段清单.md) §十：与本大纲 v2 对齐（补 bus_type/funds_nature/单位/区划/book_state/键字段行，fpaybill* 降 ❌，fconfirm 族判定）+ 03 清单 B1 键勘误记录；
3. 记忆沉淀：B1 键勘误、cbill_high 多版本冗余、票面≠实缴、B3 口径拆解四条硬规则；
4. 提醒：KB 投影仍空，本文件建完后与 fne_fund_main 一起跑 `bootstrap-kb --components semantic_model`（遗留事项）。

## 七、实测 SQL 留档（2026-10-20，yunnan0508 / ClickHouse 23.3）

```sql
-- ① 粒度与冗余：53,386 行 vs 46,357 fid；重复行三列全同（纯报文重发）
WITH d AS (SELECT fid, count() AS c, uniqExact(fstate) AS ds, uniqExact(famt) AS da,
                  uniqExact(fpid) AS dp
           FROM yunnan0508.une_cbill_high GROUP BY fid HAVING c > 1)
SELECT count() AS dup_fids, sum(c) AS dup_rows, max(c) AS max_c,
       uniqExactIf(ds, ds > 1) AS multi_state_fids,
       uniqExactIf(da, da > 1) AS multi_amt_fids,
       uniqExactIf(dp, dp > 1) AS multi_fpid_fids FROM d;
-- 结果：1495 / 8524 / 12 / 0 / 0 / 0

-- ② B1 键勘误：item.fpid 连 cbill_high.fid 为 0 行，连 fpid 命中 40,261
SELECT
  (SELECT count() FROM (SELECT DISTINCT fpid FROM yunnan0508.une_cbill_item_new) i
     INNER JOIN (SELECT DISTINCT fid  FROM yunnan0508.une_cbill_high) c ON i.fpid=c.fid) AS key_is_fid,
  (SELECT count() FROM (SELECT DISTINCT fpid FROM yunnan0508.une_cbill_item_new) i
     INNER JOIN (SELECT DISTINCT fpid FROM yunnan0508.une_cbill_high) c ON i.fpid=c.fpid) AS key_is_fpid;
-- 结果：0 / 40261

-- ③ 键域关系：cbill_high.fid ≡ item.fid（同域）；cbill_high.fpid ≡ cbill_new.fid（39,277）
--    → cbill_high.fid 是"行键"，fpid 是"票据键"

-- ④ fpaycode 连通：cbill 侧 89.3% 行无码（去重后 93.1% 票无码）；
--    paybook 侧 fpaycode=fpid 一一对应；跨表命中 2,380/8,044 码
SELECT fpaycode, count() AS rows, uniqExact(fid) AS d_fid, uniqExact(fpid) AS d_fpid
FROM yunnan0508.une_cbill_high WHERE fpaycode != ''
GROUP BY fpaycode HAVING count() > 1 ORDER BY rows DESC LIMIT 8;

-- ⑤ 票面金额污染：>100 万 70 行占 99.99%（全测试单位）；≤100 万区间 -50.03 亿（负票）
SELECT (SELECT round(sum(famt),2) FROM
          (SELECT fid, any(famt) AS famt FROM yunnan0508.une_cbill_high GROUP BY fid HAVING famt > 1000000)) AS amt_gt_100w,
       (SELECT round(sum(famt),2) FROM
          (SELECT fid, any(famt) AS famt FROM yunnan0508.une_cbill_high GROUP BY fid HAVING famt <= 1000000)) AS amt_le_100w;

-- ⑥ 状态/分类码值分布（fstate / fpaymode / frelatedbillid / fwriteoffbillid 等，见 §一/§三）

-- ⑦ v2 补测：B3 5,830 口径拆解（行级/去重行级/码级三口径）
SELECT
  (SELECT count() FROM yunnan0508.une_cbill_high c
     INNER JOIN yunnan0508.une_paybook_high p ON c.fpaycode=p.fpaycode) AS row_level_join,      -- 5830
  (SELECT count() FROM (SELECT fid, any(fpaycode) AS fpaycode FROM yunnan0508.une_cbill_high GROUP BY fid) c
     INNER JOIN yunnan0508.une_paybook_high p ON c.fpaycode=p.fpaycode) AS dedup_row_join;       -- 3655
-- 码级 2,380（cbill 侧 distinct fpaycode ∩ paybook 侧 8,044）

-- ⑧ v2 补测：fbustype 真实列 8 码分布（含票数/单位/金额）
SELECT fbustype, count() AS rows, uniqExact(fpid) AS d_fpid,
       uniqExact(fagenname) AS d_agen, round(sum(famt),2) AS amt
FROM yunnan0508.une_cbill_high GROUP BY fbustype ORDER BY rows DESC;
-- 1=40025/4=4892/2=4366/3=3509/8=480/5=74/10=35/6=5；'4' 金额 153.13 万亿（测试票源）、'5' -444.46 亿

-- ⑨ v2 补测：ffundsnature 6 码分布（cbill 侧）vs fne 侧字典码域（4 码）
SELECT ffundsnature, count() AS rows, uniqExact(fpid) AS d_fpid
FROM yunnan0508.une_cbill_high GROUP BY ffundsnature ORDER BY rows DESC;
-- 4=31812/12=15472/11=4584/2=749/3=226/13=63（空 480=脏簇）
-- fne 侧对照：SELECT ffundsnaturecode, count() FROM yunnan0508.fne_paybook_full_high GROUP BY ffundsnaturecode
--   → 12=1083/11=97/2=86/5=6（fne 侧无 4/3/13；'5' 在 cbill 侧无样本）

-- ⑩ v2 补测：paybook fstate 三态 + state=3 金额对账锚点
SELECT fstate, count() AS rows, uniqExact(fpid) AS d_fpid,
       round(sum(famt),2) AS amt FROM yunnan0508.une_paybook_high GROUP BY fstate;
-- 1=4416/1.37亿；3=3336/183.35亿（≈资金链实缴 183.32 亿）；2=1260/0.51亿

-- ⑪ v2 补测：单位/区划/项目/确认族/键基数
SELECT
  (SELECT uniqExact(fagenidcode) FROM yunnan0508.une_cbill_high) AS cb_agenid,        -- 78
  (SELECT uniqExact(frgncode) FROM yunnan0508.une_cbill_high) AS cb_rgn,              -- 10
  (SELECT uniqExact(fitemidcode) FROM yunnan0508.une_cbill_high) AS cb_item,          -- 91
  (SELECT uniqExact(fpayertype) FROM yunnan0508.une_cbill_high) AS cb_payertype,      -- 3
  (SELECT uniqExact(fagenidcode) FROM yunnan0508.une_paybook_high) AS pb_agenid,      -- 55
  (SELECT uniqExact(faccrgncode) FROM yunnan0508.une_paybook_high) AS pb_accrgn,      -- 9
  (SELECT uniqExact(fbelongrgncode) FROM yunnan0508.une_paybook_high) AS pb_belong,   -- 20
  (SELECT uniqExact(fitemidcode) FROM yunnan0508.une_paybook_high) AS pb_item,        -- 66
  (SELECT countIf(fconfirmcode='') FROM yunnan0508.une_paybook_high) AS pb_confirm_empty,  -- 8923/9012=99%
  (SELECT uniqExact(fconfirmtotalamt) FROM yunnan0508.une_paybook_high) AS pb_confirmamt;  -- 372（String 存金额）

-- ⑫ v2 补测：cbill 单位对 dim_agen（fab_agen 去重）命中率
SELECT (SELECT uniqExact(c.fagenidcode) FROM
          (SELECT fid, any(fagenidcode) AS fagenidcode FROM yunnan0508.une_cbill_high GROUP BY fid) c
        INNER JOIN (SELECT fagenidcode FROM yunnan0508.fab_agen GROUP BY fagenidcode) a
        ON c.fagenidcode=a.fagenidcode) AS agens_in_dim,   -- 59
       (SELECT uniqExact(fagenidcode) FROM
          (SELECT fid, any(fagenidcode) AS fagenidcode FROM yunnan0508.une_cbill_high GROUP BY fid)) AS agens_total;  -- 78

-- ⑬ v2 补测：paybook 死列复核（v1 曾列 ⏸ 的 fpaybill* 族实测）
SELECT countIf(fpaybillid='') AS paybill_empty, countIf(fisfinal=1) AS isfinal_one,
       uniqExact(fpospushstate) AS d_pospush FROM yunnan0508.une_paybook_high;
-- paybill_empty=9012（全空→❌）；isfinal 1 值（死列）；fconfirmtotalamt 样本：'100'/'1'/'10'/'100.66'
```

## 八、待确认问题

1. **大纲整体**（含 v1 两条勘误 + v2 五项补充实测）是否认可？
2. `bill_state`/`book_state`（三态有金额锚点）/`bus_type`/`funds_nature` 码值无字典或待业务——按 07 §3.1 是"建模+标注待确认"还是"缓建待业务"？（当前建议：全部 P0 建+实测分布标注，pay_mode 因空值 76% 缓建）
3. `faccagen*` 代理单位侧（cbill 79/107 distinct）缓建是否认可？（建议：待代理银行语义确认后再双轨）
4. 确认后即启动 `semantic_modeling` 落 `fne_bill_link.yml`。
