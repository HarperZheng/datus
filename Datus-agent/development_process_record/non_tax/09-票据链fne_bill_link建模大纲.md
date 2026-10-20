# fne_bill_link 票据链建模大纲（含 2026-10-20 实测勘误）

> **定位**：`fne_bill_link.yml`（票据链 B1-B4）建模前的大纲文档，回答三件事：**实测发现了什么口径问题、datasets/字段/指标怎么摆、实施步骤怎么走**。
> **依据链**：[03-宽表选型清单](03-宽表选型清单.md)（B 场景与键）→ 本文档（实测勘误 + 大纲）→ `subject/semantic_models/yunnan0508/fne_bill_link.yml`（待产）。
> **判定标准**：[07-建模判断标准](07-建模判断标准.md) 五步流程；本文所有码值/键/金额结论均为 **2026-10-20 对 yunnan0508 实测所得**（实测 SQL 见 §七 留档）。
> **状态**：大纲待确认（§八 三个待决问题），确认后由 `semantic_modeling` 子代理落 YAML（04 §2.4 禁止手写）。

---

## 一、实测发现的 4 个口径要点（建模前必须钉死）

| # | 发现 | 证据 | 对建模的影响 |
|---|---|---|---|
| 1 | **cbill_high 自身是多版本冗余表**：1,495 个 fid 各有 2~12 份重复，共 8,524 行冗余，重复行 famt/fstate/fpid 完全一致（纯报文重发） | 53,386 行 ≠ 46,357 distinct fid；raw 金额 1,541,083,489,625.32 vs 按 fid 去重 1,231,407,283,148.44（虚增 25%） | 参照 treasury_transfer_dedup 先例，**cbill_high 做 query-backed 去重**（fupdatetime 最新版 LIMIT 1 BY fid → 46,357 行），禁止裸 count/SUM |
| 2 | **cbill_high.fid 是"行键"而非"票据键"**：fid 与 item 明细 fid 同域（46,351/46,357 命中），fpid 才是票据单据键（=cbill_new.fid，39,277 命中）；item 明细字段已内联进 cbill_high | `item.fpid = cbill_high.fid` **0 行**（03 清单 B1 键在 high 链不成立）；`item.fpid = cbill_high.fpid` 40,261 命中 | **勘误 03 B1**：high 链内不再连 une_cbill_item_new（B1"票据+项目明细"一表全答），开票张数指标口径从 04 §5 的 `uniqExact(fid)` 改为 **`uniqExact(fpid)`** |
| 3 | **famt 是票面应收金额，且测试污染比资金链严重一个量级**：70 张 >100 万的票合计 1,236,410,460,376.66（占 99.99%），全部出自测试单位（云南测试单位0831/通用测试0801/丽江税务局-yshj），单笔最高 1,957.57 亿；≤100 万区间合计 **-50.03 亿（负票/红字票存在）** | 金额 Top15 抽样：fpayername='001'、测试单位名 | 票面金额指标必须声明"含测试大票与负票，仅供票据域内分析，**禁止与资金链实缴 183 亿混比**"；fpayername 建模须声明污染 |
| 4 | **票据↔缴款连通是约三成的子集连通**：cbill 侧 93.1% 票据 fpaycode 为空（去重后 43,145/46,357 张无码）；paybook 侧 fpaycode 100% 非空且=fpid 一一对应；跨表命中 2,380/8,044 码 | cbill 一个码挂多张票（022022032110000001→27 张票；53000023795000002059→25 张票） | 边语义 = **cbill:n → paybook:1**；跨链分析必须声明"无码票据不可达"，不硬凑 |

另：冲红（B8）空缺再次印证——`fwriteoffbillid` 全空（53,386/53,386），但 **`frelatedbillid` 有 7,488 行非空，是本库唯一的票据关联信号**（换开/关联票），纳入本批 P1。

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

## 三、字段建模清单（首批，逐列过 07 五步）

**cbill_high（去重后 46,357 行）**

| 优先级 | 字段 | 物理列 | 依据 |
|---|---|---|---|
| P0 | `bill_code`/`bill_name` 票种 | fbillcode(31) / fbillname(44) | 名称优先惯例；编码同义缓建 |
| P0 | `bill_state` 票据状态 | fstate：'1'=51,583 / '2'=1,323 / ''=480 行(仅 8 fpid) | 核心切分维度；**码值含义待业务确认**（mon_billtype 无此字典），description 写实测分布+待确认标注 |
| P0 | `pay_code` 票据关联码 | fpaycode | 跨 dataset 桥键（R1 依赖）；description 声明 93% 空码与"码→多票"扇出 |
| P0 | `bill_amt` 票面金额 | famt | 唯一金额列；ai_context 声明票面≠实缴、测试大票占 99.99%、含负票（≤100 万区间合计 -50.03 亿） |
| P0 | `bill_date` 开票日期 | toDate(fdate) | 主时间轴 is_time，grain=day |
| P0 | `item_idcode`/`item_name` 收费项目 | fitemidcode/fitemname | 明细行粒度内联，与资金链同码表注明 |
| P1 | `bill_source` 票源 | fbillsource（6 distinct） | 渠道分析候选；建模时补 distinct 分布 |
| P1 | `related_bill_id`/`related_bill_no` 关联票据 | frelatedbillid/no（7,488 行非空） | 本库唯一票据关联信号（B8 冲红空缺下的替代）；票号类字段按 07 §2 属号段，此处按"关联关系键"建模并说明 |
| P1 | `payer_type` 缴款人类型 | fpayertype | 待实测 distinct 后定 |
| ⏸ | `bill_no` 票据号 | fbillno（26,744 distinct，非唯一） | 号段类；解锁条件=票号级追溯需求 |
| ⏸ | 交款账户/银行族、fpbcbillid、fsecuritycode、fcheckcode | — | 隐私/内部码（07 §2） |
| ❌ | `fwriteoffbillid/batchcode/no`（全空）、`fdonatetype`（1 值死列）、fcustom1~N、fauthor/foperator 等审计元数据 | — | 死列/白名单 |

**paybook_high（9,012 行）**

| 优先级 | 字段 | 物理列 | 依据 |
|---|---|---|---|
| P0 | `pay_code` / `fpay_code` | fpaycode（100% 非空=8,044，与 fpid 一一对应） | R1 桥键；fpid 同义不重复建模（04/07 独源原则） |
| P0 | `book_amt`/`book_total_amt` | famt/ftotalamt | 通知书金额 |
| P0 | `book_date` | toDate(fdate) | 主时间轴 |
| P1 | `pay_mode` 缴款方式 | fpaymode：''=6,844 / 11=1,921 / 12=133 / 9=77 / 13=25 / 21=11 / 22=1 | **无字典**→07 §3.1 应缓建；因空值占 76%+码值无义，建议 ⏸，待业务确认 |
| P1 | `change_more_bill` | fchangemorebill（3 distinct） | 疑似换开标志，建模时先 distinct+样本核对语义 |
| ❌ | `fisfinal`（1 值死列）、fpaybill*（9,012 全空）、隐私族、fcustom | — | |

> **工具勘误**：`describe_table` 曾返回幽灵列（cbill_high 的 fbusinesstype、paybook_high 的 fisinvoice/fisarriveaccount/fisincome/fbillname/fbillsource 实测不存在），本清单已全部按 `system.columns` 实际列复核——建模时字段存在性一律以 `system.columns` 为准（07 §1 实测精神）。

## 四、指标清单（首批 1 个起量 + §八增量池）

| 指标 | 表达式 | subject_path | 说明 |
|---|---|---|---|
| **票据开票张数**（首批起量） | `uniqExact(fpid)` | ["非税收入","票据链","开票"] | **勘误 04 §5**：原 fid 口径会虚增 15%（行≠票） |
| 开票明细行数（增量） | `uniqExact(fid)` | 票据链/开票 | 明细行口径，与张数成对 |
| 票面开票金额（增量） | `SUM(bill_amt)` | 票据链/开票 | ai_context 硬声明：测试大票+负票，禁与资金链混比 |
| 汇缴通知书张数（增量） | `uniqExact(paybook_high.fid)` | 票据链/通知书 | |
| 关联票据行数（增量） | `countIf(related_bill_id != '')` | 票据链/关联 | 换开/关联分析 |
| 窗口族（增量） | 开票张数同比/环比 | 票据链/开票 | 时间轴 bill_date，**grain 必须进 group_by**（yunnan0508 已验证规则） |

## 五、口径红线（写入 ai_context.instructions）

1. **去重强制**：cbill_high 经 source_query 按 fid 去重后建模；任何直连物理表的金额/计数口径视为错误；
2. **金额隔离**：bill_amt=票面应收 ≠ 资金链实缴（fne_paybook_full_high.famt）；跨链对比永远 raw SQL 且只比张数不比金额；
3. **连通声明**：fpaycode 空 93%，无码票据在跨链查询中不可达，须显式告知而非静默丢行；
4. **空缺声明**：冲红/核销回写（B8）本库无数据；fstate 码值、fpaymode 码值待业务确认；
5. **污染声明**：fpayername 及金额侧测试污染比例建模时实测后写入（沿用 07 §5 规范）。

## 六、实施步骤（确认大纲后执行）

1. `task(semantic_modeling)`：创建 `subject/semantic_models/yunnan0508/fne_bill_link.yml`，按上表建 cbill_high（query-backed 去重）+ paybook_high + R1 边 + 首批指标，Dosi 原生校验；
2. 更新 [06-当前建模字段清单](06-当前建模字段清单.md)：新增 fne_bill_link 两 dataset 台账 + 03 清单 B1 键勘误记录；
3. 记忆沉淀：B1 键勘误、cbill_high 多版本冗余、票面≠实缴三条硬规则；
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
```

## 八、待确认问题

1. **大纲整体**（含两条勘误 B1 键、开票张数口径）是否认可？
2. `bill_state`（fstate 1/2/空）与 `pay_mode`（11/12/9/13/21/22）码值无字典——按 07 §3.1 是"建模+标注待确认"还是"缓建待业务"？（当前建议：fstate 建 P0+标注，pay_mode 缓建）
3. 确认后即启动 `semantic_modeling` 落 `fne_bill_link.yml`。
