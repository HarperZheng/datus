# 票据链路问数对账（datus vs cube）

> 数据源：yunnan0508，ClickHouse 23.3）
>
> 日期：2026-10-21独立实测
>
> 智能体：Datus 和 Cube（模型GLM）

## 本文档用途：

汇总两个问数智能体（datus、cube）对同一批问题的答案与生成 SQL，供审核人员集中评审——

1、判断哪些答案是对的；

2、正确的 SQL 应该是什么样；

3、哪个智能体的答案更好。

各题「对账注记」只列出双方数字与口径的客观差异（字段、时间轴、去重键等），供评审参考，不预判对错。

## 一、对账总表

| 编号 | 问题 | datus 结果 | cube 结果 | 对照关系 |
|---|---|---|---|---|
| q01 | 2022年全年非税缴款金额和笔数是多少？ | 182.09 亿 / 355 笔 | 182.09 亿 / 334 笔 | 金额一致；笔数不同（时间轴与去重键均不同） |
| q02 | 非税缴款金额按月展示，并给出每月环比 | 53 个月（至 2026-08），2022-04 尖峰 159.86 亿 | 57 个月（至 2026-09） | 口径不同（时间轴不同），月度数字不可直接对照 |
| q03 | 清分金额2022年对比2021年同比增长多少？ | 2021=0、2022=159.87 亿；增长率不可算 | 返回 0 行，无法计算 | 对象与时间轴不同；一方有数一方空集 |
| q04 | 缴库金额按年汇总，2022到2026各年是多少？ | 2022=78,449.12、2023=80,659.18、2024=3,763.30、2025 无、2026=29,372,234.54 | 2022=46,053.04、2023=34,178.26、2024=3,463.30、2025=0、2026=29,372,234.54 | 2026 一致；2022-2024 不一致（时间轴与去重口径不同） |
| q05 | 全库累计清分了多少金额、清分率是多少？ | 清分 160.16 亿 / 缴款 183.32 亿 / 清分率 0.8737 | 同三数（160.16 亿 / 183.32 亿 / 0.8737） | 完全一致 |
| q06 | 2022年缴款金额排名前10的执收单位有哪些？ | 9 单位，Top1 测试云南测试环境 182.09 亿 / 272 笔 | 9 单位，Top1（124045）182.09 亿 / 253 笔 | 主体金额一致；笔数不同（时间轴与去重键不同） |
| q07 | 测试云南省教育厅1直属下级单位合计缴款金额是多少？ | 44 家下级合计 183.30 亿（直缴 160.47 亿） | nomatch | 一方有数，一方声明不可答 |
| q08 | 各执收预算单位2022年的清分金额对比 | 2022 年 9 单位，Top1 159.87 亿、清分率 87.80% | 全量 25 单位，Top1 划拨 63,371 元 / 分入 159.87 亿 | 时间范围与金额口径不同，数字不可直接对照 |
| q09 | 哪些非叶子单位自己直接收了款？各收了多少？ | 无最终答案（引擎中断） | nomatch | 双方均未给出答案 |
| q10 | 按执收单位统计未到账的缴款笔数 | 1 笔（124045） | 1 笔（124045） | 一致 |
| q11 | 各预算科目清分金额排行，政府性基金收入103大类下哪些叶子科目收得最多？ | 10301 层级：103010201 最多，159.86 亿 / 99.81% | 103 前缀 20 组，103010201 最多（同值 / 99.81%） | 头部数字一致；分类树处理方式不同 |
| q12 | 民航发展基金历年缴款金额趋势 | 2024 峰值 2,912.22 万，历年合计约 3,236 万 | 2024 峰值 2,896.20 万，历年合计 3,085.09 万 | 数字不同（数据表与时间轴双差） |
| q13 | 按收入分类统计缴款金额：政府性基金收入、专项收入、行政事业性收费收入、罚没收入各占多少？ | 政府性基金 182.85 亿 / 99.74%、专项 0.31 亿、行政事业性收费 0.16 亿、罚没 300 元 | 同四类数字（政府性基金 182.85 亿 / 99.74% 等） | 主分类数字一致；datus 合计行与其分项之和不勾稽 |
| q14 | 按资金性质分组统计缴款金额 | 12=183.16 亿、2=1,486.7 万、11=129.3 万、5=600 元 | 政府性基金 160.16 亿、一般公共预算 118.4 万、财政专户 39,329、空 23.15 亿 | 口径不同（票面 vs 归属），数字不可直接对照 |
| q15 | 缴款金额前5的收费项目，按直缴汇缴拆分展示 | Top5：农网还贷 160.45 亿、煤炭、民航 3,085.08 万、住宿费、保教费（各按直缴/汇缴拆分） | Top5：农网还贷、煤炭、民航、农网还贷 a、住宿费 | 口径不同（主键体系不同）；主体项目金额量级一致 |
| q16 | 按归属区划统计清分金额 | 省本级 160.16 亿、中央 4,516.12、昆明市本级 1,778.70、五华区 495.33、云龙县 0 | 同五组同值 | 完全一致（组级） |
| q17 | 按执收区划名称统计缴款金额 | 云南省本级 183.31 亿、云龙县 1,156,320、五华区 79,406.12、昆明市本级 5,184、官渡区 400 | 省本级 160.16 亿、空 23.15 亿、云龙 1,156,320、中央 9,617.68、昆明 2,541、五华 990.66 | 分组字段不同，数字不可直接对照 |
| q18 | 五华区的执收单位有哪些、各收了多少钱？ | 3 单位 6 笔 79,406.12（最大 77,324.80） | 3 单位 4 笔 79,406.12（最大 77,324.80） | 金额一致；笔数不同 |
| q19 | 各收款银行2022年各收了多少笔、多少钱？ | 6 家银行 355 笔 182.09 亿，建行 226 笔 / 182.08 亿 | 6 家 334 笔，建行 211 笔 / 182.08 亿 | 主体金额接近；笔数分布不同（时间轴与去重键不同） |
| q20 | 归属区划在云南省本级以外的缴款金额有多少？ | 非省本级 116.9 万 / 41 笔 + 空 23.15 亿 / 544 笔，合计 23.16 亿 | 23.16 亿（504 笔，含空）；剔除空 116.9 万（39 笔） | 金额一致；笔数口径不同 |
| q21 | 已划拨和未划拨的金额各是多少？ | 已划拨 21,024.00 / 未划拨 38,142.30（共 121 批） | 已划拨 72,507.62 / 未划拨 160.16 亿（全量差值） | 主语与去重口径双重不同，数字不可直接对照 |
| q22 | 缴库报文里已确认入库和待国库确认的金额各是多少？ | 已确认入库 11,064.00 / 待确认 35,240.09；另未缴库 29,488,802.05 | 已入国库 46,304.09 / 未入库 29,409,625.05 | 状态字段与组划分均不同，数字不可直接对照 |
| q23 | 汇总批次一共多少个？ | 428 个批次 | 550 条记录 | 行数一致（550）；批次数 vs 记录数口径不同 |
| q24 | 未清分的缴款笔数和金额是多少？ | 515 笔 / 23.15 亿 | 439 缴款书 / 23.15 亿 | 金额基本一致；判据与笔数口径不同 |
| q25 | 清分率按业务类型分组对比：直缴和汇缴各是多少？ | 直缴 99.80% / 汇缴 ≈0.0035% / 整体 87.37% | 比值不可查，拍板口径 0.00%；参考分布直缴 1,063 行 / 汇缴 209 行 | 分布行数一致；比值口径不同 |

## 二、逐题对照

### q01　2022年全年非税缴款金额和笔数是多少？

**datus**（成功(指标路径)，116.0s）

| 指标 | 结果 |
|---|---|
| **非税缴款金额** | **18,208,936,572.27 元 ≈ 182.09 亿元** |
| **非税缴款笔数** | **355 笔** |

**datus 生成 SQL**

```sql
SELECT
  sum(famt)                     AS 非税缴款金额,
  COUNT(DISTINCT fid)           AS 非税缴款笔数
FROM yunnan0508.fne_paybook_full_high
WHERE toDate(ffilldate) >= '2022-01-01'
  AND toDate(ffilldate) <  '2023-01-01'
```

**cube**（ask→追问→answer，42.2s）

**2022年非税缴款合计（收入类别三类口径，pay_date）**（1 行）
| amt | paybook_count |
|---|---|
| 18208936572.27 | 334 |

**cube 生成 SQL**

```sql
-- table[0] 2022年非税缴款合计（收入类别三类口径，pay_date）
SELECT sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (toDateOrNull(`fiscal_collection`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_collection`.`fdate`) <= parseDateTimeBestEffort(?))
ORDER BY  1  DESC
LIMIT 1002022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z
```

**对账注记（客观差异）**

- 金额分毫不差：均为 18,208,936,572.27 元。
- 笔数不同：355（datus，COUNT(DISTINCT fid)）vs 334（cube，paybook_count 缴款书数）。
- 时间轴不同：datus 用 fill_date（填开日），cube 用 pay_date（缴款日）。

### q02　非税缴款金额按月展示，并给出每月环比

**datus**（成功，216.0s）

全部 53 个自然月（含 5 个无数据月）已拼齐并交叉验证：

| 月份 | 金额（元） | 环比增长率 |
|---|---:|---:|
| 2021-12 | 833.00 | — |
| 2022-01 | 13,301.00 | +1,496.76% |
| 2022-02 | 40,779.00 | +206.59% |
| 2022-03 | 19,365.00 | −52.51% |
| **2022-04** | **15,985,631,865.00** | +82,548,993.03% |
| 2022-05 | 494.00 | −100.00% |
| 2022-06 | 4,112.90 | +732.57% |
| 2022-07 | 23.00 | −99.44% |
| 2022-08 | 17,417.79 | +75,629.52% |
| 2022-09 | 5,653.68 | −67.54% |
| 2022-10 | 38,188.35 | +575.46% |
| 2022-11 | 236,794.19 | +520.07% |
| **2022-12** | **2,222,928,578.36** | +938,659.76% |
| 2023-01 | 0.00（无数据） | −100.00% |
| 2023-02 | 44,876.00 | —（上月无基数） |
| 2023-03 | 4,086.00 | −90.89% |
| 2023-04 | 5,819.00 | +42.41% |
| 2023-05 | 964.00 | −83.43% |
| 2023-06 | 43,459.45 | +4,408.24% |
| 2023-07 | 1,171,872.00 | +2,596.47% |
| 2023-08 | 24,457.08 | −97.91% |
| 2023-09 | 128,914.88 | +427.11% |
| 2023-10 | 600.00 | −99.53% |
| 2023-11 | 37,408.60 | +6,134.77% |
| 2023-12 | 3,353.30 | −91.04% |
| 2024-01 | 164,244.58 | +4,798.00% |
| **2024-02** | **46,039,171.70** | +27,930.86% |
| 2024-03 | 3,164.62 | −99.99% |
| **2024-04** | **28,982,824.78** | +915,739.02% |
| 2024-05 | 22,063.00 | −99.92% |
| 2024-06 | 5,836.24 | −73.55% |
| 2024-07 | 1,405.28 | −75.92% |
| 2024-08 | 610,281.59 | +43,327.76% |
| 2024-09 | 6,846.64 | −98.88% |
| 2024-10 | 139,444.89 | +1,936.69% |
| 2024-11 | 9,105.86 | −93.47% |
| 2024-12 | 140,047.64 | +1,437.99% |
| **2025-01** | **30,695,653.30** | +21,818.01% |
| 2025-02 | 453.00 | −100.00% |
| 2025-03 | 27,734.88 | +6,022.49% |
| 2025-04 | 15,413.20 | −44.43% |
| 2025-05 | 0.00（无数据） | −100.00% |
| 2025-06 | 5,256.29 | —（上月无基数） |
| 2025-07 | 1,084.00 | −79.38% |
| 2025-08 | 0.00（无数据） | −100.00% |
| 2025-09 | 1,777.33 | —（上月无基数） |
| 2025-10 | 4,492.36 | +152.76% |
| 2025-11 | 1,501.00 | −66.59% |
| 2025-12 | 1,000.02 | −33.38% |
| 2026-01 | 4,632.00 | +363.19% |
| 2026-02 | 0.00（无数据） | −100.00% |
| 2026-03 | 0.00（无数据） | — |
| 2026-04 | 1,982.32 | —（上月无基数） |
| 2026-05 | 7,222.00 | +264.32% |
| **2026-06** | **14,909,895.85** | +206,351.06% |
| 2026-07 | 752.52 | −99.99% |
| 2026-08 | 700.66 | −6.89% |

**datus 生成 SQL**

```sql
WITH monthly AS (
    SELECT toStartOfMonth(toDate(ffilldate)) AS ym, SUM(famt) AS amt
    FROM fne_paybook_full_high
    GROUP BY ym
)
SELECT
    formatDateTime(a.ym, '%Y-%m')                          AS `月份`,
    ROUND(COALESCE(b.amt, 0), 2)                           AS `非税缴款金额_元`,
    lagInFrame(COALESCE(b.amt, 0), 1) OVER (
        ORDER BY a.ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                      AS `上月金额_元`,
    IF(COALESCE(b.amt, 0) = 0
       OR lagInFrame(COALESCE(b.amt, 0), 1) OVER (
              ORDER BY a.ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) IN (0, NULL),
       NULL,
       ROUND((COALESCE(b.amt, 0) - lagInFrame(COALESCE(b.amt, 0), 1) OVER (
              ORDER BY a.ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW))
             / lagInFrame(COALESCE(b.amt, 0), 1) OVER (
              ORDER BY a.ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100, 2)
    )                                                      AS `环比增长率_%`
FROM (
    SELECT toStartOfMonth(addMonths(toDate('2021-12-01'), number)) AS ym
    FROM numbers(57)          -- 2021-12 起共 57 个自然月，补齐无数据月份
) a
LEFT JOIN monthly b USING (ym)
ORDER BY a.ym
```

**cube**（answer，48.4s）

**非税缴款金额按月 + 月环比（pay_date 月粒度，全量 57 个月）**（57 行）
| month | amt | amt_mom_diff | amt_mom_rate |
|---|---|---|---|
| 2021-12 | 833 |  |  |
| 2022-01 | 13301 | 12468 | 1496.76 |
| 2022-02 | 40779 | 27478 | 206.59 |
| 2022-03 | 19815 | -20964 | -51.41 |
| 2022-04 | 15985631415 | 15985611600 | 80674295.23 |
| 2022-05 | 494 | -15985630921 | -100 |
| 2022-06 | 4112.9 | 3618.9 | 732.57 |
| 2022-07 | 23 | -4089.9 | -99.44 |
| 2022-08 | 17617.79 | 17594.79 | 76499.09 |
| 2022-09 | 5453.68 | -12164.11 | -69.04 |
| 2022-10 | 38188.35 | 32734.67 | 600.23 |
| 2022-11 | 236799.19 | 198610.84 | 520.08 |
| 2022-12 | 2222928573.36 | 2222691774.17 | 938639.94 |
| 2023-01 |  |  |  |
| 2023-02 | 44876 |  |  |
| 2023-03 | 4086 | -40790 | -90.89 |
| 2023-04 | 5819 | 1733 | 42.41 |
| 2023-05 | 1014 | -4805 | -82.57 |
| 2023-06 | 43409.45 | 42395.45 | 4181.01 |
| 2023-07 | 1171872 | 1128462.55 | 2599.58 |
| 2023-08 | 24457.08 | -1147414.92 | -97.91 |
| 2023-09 | 128914.88 | 104457.8 | 427.11 |
| 2023-10 | 600 | -128314.88 | -99.53 |
| 2023-11 | 37408.6 | 36808.6 | 6134.77 |
| 2023-12 | 3353.3 | -34055.3 | -91.04 |
| 2024-01 | 164244.582 | 160891.282 | 4798 |
| 2024-02 | 46039471.7 | 45875227.118 | 27931.04 |
| 2024-03 | 2864.62 | -46036607.08 | -99.99 |
| 2024-04 | 28982824.78 | 28979960.16 | 1011651.11 |
| 2024-05 | 22063 | -28960761.78 | -99.92 |
| 2024-06 | 5836.24 | -16226.76 | -73.55 |
| 2024-07 | 1405.28 | -4430.96 | -75.92 |
| 2024-08 | 610281.59 | 608876.31 | 43327.76 |
| 2024-09 | 6446.64 | -603834.95 | -98.94 |
| 2024-10 | 141015.21 | 134568.57 | 2087.42 |
| 2024-11 | 7935.54 | -133079.67 | -94.37 |
| 2024-12 | 140047.64 | 132112.1 | 1664.82 |
| 2025-01 | 30695653.3 | 30555605.66 | 21818.01 |
| 2025-02 | 423 | -30695230.3 | -100 |
| 2025-03 | 27734.88 | 27311.88 | 6456.71 |
| 2025-04 | 15413.2 | -12321.68 | -44.43 |
| 2025-05 |  |  |  |
| 2025-06 | 5196.29 |  |  |
| 2025-07 | 1084 | -4112.29 | -79.14 |
| 2025-08 |  |  |  |
| 2025-09 | 1777.33 |  |  |
| 2025-10 | 4582.36 | 2805.03 | 157.82 |
| 2025-11 | 1501 | -3081.36 | -67.24 |
| 2025-12 | 1000.02 | -500.98 | -33.38 |
| 2026-01 | 4632 | 3631.98 | 363.19 |
| 2026-02 |  |  |  |
| 2026-04 | 1982.32 |  |  |
| 2026-05 | 7222 | 5239.68 | 264.32 |
| 2026-06 | 14909895.85 | 14902673.85 | 206351.06 |
| 2026-07 | 752.52 | -14909143.33 | -99.99 |
| 2026-08 | 700.66 | -51.86 | -6.89 |
| 2026-09 |  |  |  |

**cube 生成 SQL**

```sql
-- table[0] 非税缴款金额按月 + 月环比（pay_date 月粒度，全量 57 个月）
 WITH 
cte_0 AS (  SELECT date_trunc('month', "fiscal_collection__pay_date_month") "fiscal_collection_view__pay_date_month", sum("fiscal_collection__amt") "fiscal_collection__amt" 
  FROM  dev_pre_aggregations.fiscal_collection_main__usage_2  AS "fiscal_collection__main"
  GROUP BY 1
  ORDER BY  1  ASC),
cte_1 AS (  SELECT date_trunc('month', ("fiscal_collection__pay_date_month" + interval '1 month')) "fiscal_collection_view__pay_date_month", sum("fiscal_collection__amt") "fiscal_collection__amt" 
  FROM  dev_pre_aggregations.fiscal_collection_main__usage_1  AS "fiscal_collection__main"
  GROUP BY 1
  ORDER BY  1  ASC),
cte_2 AS (  SELECT "fk_aggregate"."fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month", sum("fk_aggregate"."fiscal_collection__amt") "fiscal_collection__amt_lm" 
  FROM  cte_1  AS "fk_aggregate"
  GROUP BY 1
  ORDER BY  1  ASC),
cte_3 AS (  SELECT "fk_aggregate_keys"."fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month", "q_0"."fiscal_collection__amt" - "q_1"."fiscal_collection__amt_lm" "fiscal_collection__amt_mom_diff" 
  FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM  cte_0  AS "cte_0"
   UNION ALL 
  SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM  cte_2  AS "cte_2") AS "fk_aggregate_keys_source") AS "fk_aggregate_keys"
  LEFT JOIN  cte_0  AS "q_0" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_0"."fiscal_collection_view__pay_date_month"))
  LEFT JOIN  cte_2  AS "q_1" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_1"."fiscal_collection_view__pay_date_month"))),
cte_4 AS (  SELECT "fk_aggregate_keys"."fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month", 100.0 * ("q_0"."fiscal_collection__amt" - "q_1"."fiscal_collection__amt_lm") / NULLIF("q_1"."fiscal_collection__amt_lm", 0) "fiscal_collection__amt_mom_rate" 
  FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM  cte_0  AS "cte_0"
   UNION ALL 
  SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
  FROM  cte_2  AS "cte_2") AS "fk_aggregate_keys_source") AS "fk_aggregate_keys"
  LEFT JOIN  cte_0  AS "q_0" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_0"."fiscal_collection_view__pay_date_month"))
  LEFT JOIN  cte_2  AS "q_1" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_1"."fiscal_collection_view__pay_date_month"))),
cte_5 AS (  SELECT date_trunc('month', "fiscal_collection__pay_date_month") "fiscal_collection_view__pay_date_month", sum("fiscal_collection__amt") "fiscal_collection__amt" 
  FROM  dev_pre_aggregations.fiscal_collection_main__usage_0  AS "fiscal_collection__main"
  GROUP BY 1)
SELECT "fk_aggregate_keys"."fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month", "q_2"."fiscal_collection__amt" "fiscal_collection_view__amt", "q_0"."fiscal_collection__amt_mom_diff" "fiscal_collection_view__amt_mom_diff", "q_1"."fiscal_collection__amt_mom_rate" "fiscal_collection_view__amt_mom_rate" 
FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
FROM (SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
FROM  cte_3  AS "cte_3"
 UNION ALL 
SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
FROM  cte_4  AS "cte_4"
 UNION ALL 
SELECT DISTINCT "fiscal_collection_view__pay_date_month" "fiscal_collection_view__pay_date_month" 
FROM  cte_5  AS "cte_5") AS "fk_aggregate_keys_source") AS "fk_aggregate_keys"
LEFT JOIN  cte_3  AS "q_0" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_0"."fiscal_collection_view__pay_date_month"))
LEFT JOIN  cte_4  AS "q_1" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_1"."fiscal_collection_view__pay_date_month"))
LEFT JOIN  cte_5  AS "q_2" ON (("fk_aggregate_keys"."fiscal_collection_view__pay_date_month" IS NOT DISTINCT FROM "q_2"."fiscal_collection_view__pay_date_month"))
ORDER BY  1  ASC
LIMIT 100
```

**对账注记（客观差异）**

- 时间轴不同（fill_date vs pay_date），各月金额随之不同（如 2022-04：datus 15,985,631,865.00）。
- 覆盖范围不同：datus 至 2026-08，cube 至 2026-09。
- 环比空值处理不同：datus 显示"—"（含"上月无基数"），cube 返回 null。

### q03　清分金额2022年对比2021年同比增长多少？

**datus**（成功，93.9s）

**结论：2021 年清分金额为 0，同比增长额 +159.87 亿元，增长率无法计算（基数为 0）**

| 年份 | 清分金额（元） | 明细行数 |
|---|---:|---:|
| 2021 | 0（无任何 `fcleardate` 落在 2021 年的记录） | 0 |
| 2022 | **15,986,577,101.87（≈159.87 亿）** | 320 |

**datus 生成 SQL**

```sql
SELECT substring(fcleardate, 1, 4) AS clear_year,
       round(sum(fimamt), 2) AS clear_amount
FROM yunnan0508.fne_paybook_full_high
WHERE substring(fcleardate, 1, 4) IN ('2021', '2022')
GROUP BY clear_year
ORDER BY clear_year
```

**cube**（answer，43.5s）

**清分金额 2022 年同比（pay_date 年度轴，分入/划拨双口径）**（0 行）

**cube 生成 SQL**

```sql
-- table[0] 清分金额 2022 年同比（pay_date 年度轴，分入/划拨双口径）
 WITH 
cte_0 AS (  SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(toDateOrNull(`fiscal_allocation`.`fdate`), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_allocation_view__pay_date_year`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation__im_amt` 
  FROM  (SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT frecsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
             FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
  )  AS `fiscal_allocation`
  WHERE (toDateOrNull(`fiscal_allocation`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_allocation`.`fdate`) <= parseDateTimeBestEffort(?))
  GROUP BY 1
  ORDER BY  1  ASC),
cte_1 AS (  SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_allocation_view__pay_date_year`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation__im_amt` 
  FROM  (SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT frecsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
             FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
  )  AS `fiscal_allocation`
  WHERE (((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)) >= parseDateTimeBestEffort(?) AND ((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)) <= parseDateTimeBestEffort(?))
  GROUP BY 1
  ORDER BY  1  ASC),
cte_2 AS (  SELECT `fk_aggregate`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, sum(`fk_aggregate`.`fiscal_allocation__im_amt`) `fiscal_allocation__im_amt_ly` 
  FROM  cte_1  AS `fk_aggregate`
  GROUP BY 1
  ORDER BY  1  ASC),
cte_3 AS (  SELECT `fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, `q_0`.`fiscal_allocation__im_amt` - `q_1`.`fiscal_allocation__im_amt_ly` `fiscal_allocation__im_amt_yoy_diff` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_0  AS `cte_0`
   UNION ALL 
  SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_2  AS `cte_2`) AS `fk_aggregate_keys_source`) AS `fk_aggregate_keys`
  LEFT JOIN  cte_0  AS `q_0` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_0`.`fiscal_allocation_view__pay_date_year`))
  LEFT JOIN  cte_2  AS `q_1` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_1`.`fiscal_allocation_view__pay_date_year`))),
cte_4 AS (  SELECT `fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, 100.0 * (`q_0`.`fiscal_allocation__im_amt` - `q_1`.`fiscal_allocation__im_amt_ly`) / NULLIF(`q_1`.`fiscal_allocation__im_amt_ly`, 0) `fiscal_allocation__im_amt_yoy_rate` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_0  AS `cte_0`
   UNION ALL 
  SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_2  AS `cte_2`) AS `fk_aggregate_keys_source`) AS `fk_aggregate_keys`
  LEFT JOIN  cte_0  AS `q_0` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_0`.`fiscal_allocation_view__pay_date_year`))
  LEFT JOIN  cte_2  AS `q_1` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_1`.`fiscal_allocation_view__pay_date_year`))),
cte_5 AS (  SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(toDateOrNull(`fiscal_allocation`.`fdate`), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_allocation_view__pay_date_year`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation__trans_amt` 
  FROM  (SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT frecsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
             FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
  )  AS `fiscal_allocation`
  WHERE (toDateOrNull(`fiscal_allocation`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_allocation`.`fdate`) <= parseDateTimeBestEffort(?))
  GROUP BY 1
  ORDER BY  1  ASC),
cte_6 AS (  SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_allocation_view__pay_date_year`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation__trans_amt` 
  FROM  (SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT frecsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
             FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
  )  AS `fiscal_allocation`
  WHERE (((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)) >= parseDateTimeBestEffort(?) AND ((toDateOrNull(`fiscal_allocation`.`fdate`) + INTERVAL 1 YEAR)) <= parseDateTimeBestEffort(?))
  GROUP BY 1
  ORDER BY  1  ASC),
cte_7 AS (  SELECT `fk_aggregate`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, sum(`fk_aggregate`.`fiscal_allocation__trans_amt`) `fiscal_allocation__trans_amt_ly` 
  FROM  cte_6  AS `fk_aggregate`
  GROUP BY 1
  ORDER BY  1  ASC),
cte_8 AS (  SELECT `fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, `q_0`.`fiscal_allocation__trans_amt` - `q_1`.`fiscal_allocation__trans_amt_ly` `fiscal_allocation__trans_amt_yoy_diff` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_5  AS `cte_5`
   UNION ALL 
  SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_7  AS `cte_7`) AS `fk_aggregate_keys_source`) AS `fk_aggregate_keys`
  LEFT JOIN  cte_5  AS `q_0` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_0`.`fiscal_allocation_view__pay_date_year`))
  LEFT JOIN  cte_7  AS `q_1` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_1`.`fiscal_allocation_view__pay_date_year`))),
cte_9 AS (  SELECT `fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, 100.0 * (`q_0`.`fiscal_allocation__trans_amt` - `q_1`.`fiscal_allocation__trans_amt_ly`) / NULLIF(`q_1`.`fiscal_allocation__trans_amt_ly`, 0) `fiscal_allocation__trans_amt_yoy_rate` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_5  AS `cte_5`
   UNION ALL 
  SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
  FROM  cte_7  AS `cte_7`) AS `fk_aggregate_keys_source`) AS `fk_aggregate_keys`
  LEFT JOIN  cte_5  AS `q_0` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_0`.`fiscal_allocation_view__pay_date_year`))
  LEFT JOIN  cte_7  AS `q_1` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_1`.`fiscal_allocation_view__pay_date_year`))),
cte_10 AS (  SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(toDateOrNull(`fiscal_allocation`.`fdate`), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_allocation_view__pay_date_year`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation__im_amt`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation__trans_amt` 
  FROM  (SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT frecsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
             FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
  )  AS `fiscal_allocation`
  WHERE (toDateOrNull(`fiscal_allocation`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_allocation`.`fdate`) <= parseDateTimeBestEffort(?))
  GROUP BY 1)
SELECT `fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year`, `q_4`.`fiscal_allocation__im_amt` `fiscal_allocation_view__im_amt`, `q_0`.`fiscal_allocation__im_amt_yoy_diff` `fiscal_allocation_view__im_amt_yoy_diff`, `q_1`.`fiscal_allocation__im_amt_yoy_rate` `fiscal_allocation_view__im_amt_yoy_rate`, `q_4`.`fiscal_allocation__trans_amt` `fiscal_allocation_view__trans_amt`, `q_2`.`fiscal_allocation__trans_amt_yoy_diff` `fiscal_allocation_view__trans_amt_yoy_diff`, `q_3`.`fiscal_allocation__trans_amt_yoy_rate` `fiscal_allocation_view__trans_amt_yoy_rate` 
FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM (SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM  cte_3  AS `cte_3`
 UNION ALL 
SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM  cte_4  AS `cte_4`
 UNION ALL 
SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM  cte_8  AS `cte_8`
 UNION ALL 
SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM  cte_9  AS `cte_9`
 UNION ALL 
SELECT DISTINCT `fiscal_allocation_view__pay_date_year` `fiscal_allocation_view__pay_date_year` 
FROM  cte_10  AS `cte_10`) AS `fk_aggregate_keys_source`) AS `fk_aggregate_keys`
LEFT JOIN  cte_3  AS `q_0` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_0`.`fiscal_allocation_view__pay_date_year`))
LEFT JOIN  cte_4  AS `q_1` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_1`.`fiscal_allocation_view__pay_date_year`))
LEFT JOIN  cte_8  AS `q_2` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_2`.`fiscal_allocation_view__pay_date_year`))
LEFT JOIN  cte_9  AS `q_3` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_3`.`fiscal_allocation_view__pay_date_year`))
LEFT JOIN  cte_10  AS `q_4` ON ((`fk_aggregate_keys`.`fiscal_allocation_view__pay_date_year`) = (`q_4`.`fiscal_allocation_view__pay_date_year`))
LIMIT 102022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z2022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z2022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z2022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z2022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z
```

**对账注记（客观差异）**

- 查询对象不同：datus 查缴款宽表的 fimamt 按 fcleardate 归年；cube 查划拨视图（trans_amt / im_amt）按 pay_date 归年。
- datus 得出 2022 年清分 15,986,577,101.87 元；cube 在其查询组合下返回空集。
- 参照：cube q05 全库 im_amt 合计 16,016,079,467.68 元与 datus 的 2022 清分数字量级接近（约 99.8%），但两者口径不同（全库无时间轴 vs 2022 年 fcleardate）。

### q04　缴库金额按年汇总，2022到2026各年是多少？

**datus**（成功，85.2s）

| 年份 | 缴库笔数 | 缴库金额（元） |
|------|---------|---------------|
| 2022 | 34 | 78,449.12 |
| 2023 | 10 | 80,659.18 |
| 2024 | 15 | 3,763.30 |
| 2025 | — | **无缴库报文** |
| 2026 | 17 | 29,372,234.54 |
| **合计** | **76** | **29,535,106.14** |

**datus 生成 SQL**

```sql
SELECT
    toYear(toDate(fmsgdate)) AS yr,
    count() AS bill_cnt,
    round(SUM(ftotalamt), 2) AS treasury_amt
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY fid) AS _rn
    FROM yunnan0508.fne_treasury_transfer_new
)
WHERE _rn = 1
GROUP BY yr
ORDER BY yr
```

**cube**（answer，24.7s）

**各年缴库金额（口径：缴库明细 amt，按缴库日期 build_date 年分组，单位元）**（5 行）
| year | amt |
|---|---|
| 2022 | 46053.04 |
| 2023 | 34178.26 |
| 2024 | 3463.3 |
| 2025 | 0 |
| 2026 | 29372234.54 |

**cube 生成 SQL**

```sql
-- table[0] 各年缴库金额（口径：缴库明细 amt，按缴库日期 build_date 年分组，单位元）
SELECT date_trunc('year', "fiscal_treasury__build_date_month") "fiscal_treasury_view__build_date_year", sum("fiscal_treasury__amt") "fiscal_treasury_view__amt" 
FROM  dev_pre_aggregations.fiscal_treasury_main  AS "fiscal_treasury__main"
WHERE ("fiscal_treasury__build_date_month" >= CAST(? as TIMESTAMP) AND "fiscal_treasury__build_date_month" <= CAST(? as TIMESTAMP))
GROUP BY 1
ORDER BY  1  ASC
LIMIT 1002022-01-01T00:00:00.0002026-12-31T23:59:59.999
```

**对账注记（客观差异）**

- 2026 年金额一致：29,372,234.54 元。
- 2022-2024 三年不一致：datus 78,449.12 / 80,659.18 / 3,763.30 vs cube 46,053.04 / 34,178.26 / 3,463.30。
- 时间轴不同：datus fmsgdate（报文日期）vs cube build_date（建单日）。
- 去重口径不同：datus 按 fid 去重（76 行）vs cube 视图缴库明细直查。

### q05　全库累计清分了多少金额、清分率是多少？

**datus**（成功，158.1s）

| 指标 | 数值 |
|---|---|
| **清分金额**（SUM(fimamt)） | **16,016,079,467.68 元 ≈ 160.16 亿元** |
| **非税缴款金额**（SUM(famt)，分母） | 18,332,207,203.13 元 ≈ 183.32 亿元 |
| **清分率** = 清分 ÷ 缴款 | **0.8737 ≈ 87.37%** |

**datus 生成 SQL**

```sql
SELECT
  COALESCE(SUM(fimamt), 0) AS cleared_amt,
  COALESCE(SUM(famt), 0)   AS pay_amt,
  COALESCE(SUM(fimamt), 0) / COALESCE(SUM(famt), 0) AS clear_rate
FROM fne_paybook_full_high
```

**cube**（ask→追问→answer，22.6s）

**口径A：全库累计清分 vs 缴款总额（清分率）**（1 行）
| im_amt | trans_amt | count | amt | 清分率(%) |
|---|---|---|---|---|
| 16016079467.68 | 72507.62 | 728 | 18332207203.13 | 87.37 |

**cube 生成 SQL**

```sql
-- table[0] 口径A：全库累计清分 vs 缴款总额（清分率）
SELECT sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation_view__trans_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
ORDER BY  1  DESC
LIMIT 1
```

**对账注记（客观差异）**

- 三个数完全一致：分子、分母、比值。
- 来源不同：datus 同表两列（fimamt / famt）vs cube 跨两视图两成员（im_amt / amt）分查后相除。

### q06　2022年缴款金额排名前10的执收单位有哪些？

**datus**（成功，245.7s）

| 排名 | 执收单位编码 | 执收单位名称 | 缴款金额（元） | 缴款明细笔数 |
|---|---|---|---|---|
| 1 | 36299bf1...16cc588 | 测试云南测试环境(试用版) | 18,208,882,274.85（约 182.09 亿） | 272 |
| 2 | 6e4ba023... | 云南测试单位1209 | 24,034.92 | 4 |
| 3 | 5c18ec29... | 测试1125 | 11,763.68 | 20 |
| 4 | 1cc48566... | 云南医疗单位0729 | 6,864.26 | 19 |
| 5 | 62aa3631... | 测试分成测试 | 5,184.00 | 9 |
| 6 | d5058204... | 测试云南通用测试单位0720 | 2,057.68 | 13 |
| 7 | 57661ea5... | 测试云南医疗单位0805 | 1,915.12 | 9 |
| 8 | 67455953... | 测试测试单位0722 | 1,377.76 | 7 |
| 9 | ec8eb0f0... | 测试云南通用Oracle0728 | 1,100.00 | 2 |

实际只有 9 个单位（2022 年内有缴款数据的执收单位不足 10 个）。

**datus 生成 SQL**

```sql
SELECT
    fchgagenidcode AS agen_code,
    groupUniqArray(fchgagenname) AS agen_names,
    round(SUM(famt), 2) AS amt_sum,
    uniqExact(fid) AS detail_cnt
FROM fne_paybook_full_high
WHERE ffilldate >= '2022-01-01' AND ffilldate < '2023-01-01'
GROUP BY fchgagenidcode
ORDER BY amt_sum DESC
LIMIT 10
```

**cube**（answer，25.0s）

**2022年缴款金额Top执收单位（口径：缴款明细金额 amt，时间轴 pay_date）**（9 行）
| chg_agency_code | chg_agency_name | amt | paybook_count |
|---|---|---|---|
| 124045 | 001 / 测试云南测试环境 / 测试云南测试环境(试用版) / 测试云南测试环境(试用版)(试用版) | 18208882274.85 | 253 |
| 425002 | 云南测试单位1209 | 24034.92 | 4 |
| 124100 | 测试1125 | 11763.68 | 18 |
| 125019 | 云南医疗单位0729 / 测试云南医疗单位0729 | 6864.26 | 19 |
| 001 | 测试分成测试 | 5184 | 9 |
| 124576 | 测试云南通用测试单位0720 | 2057.68 | 13 |
| 125020 | 测试云南医疗单位0805 | 1915.12 | 9 |
| 124577 | 测试测试单位0722 | 1377.76 | 7 |
| 124579 | 测试云南通用Oracle0728 | 1100 | 2 |

**cube 生成 SQL**

```sql
-- table[0] 2022年缴款金额Top执收单位（口径：缴款明细金额 amt，时间轴 pay_date）
SELECT `fiscal_collection`.`fchgagencode` `fiscal_collection_view__chg_agency_code`, `fiscal_collection`.chg_agency_name_canon `fiscal_collection_view__chg_agency_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (toDateOrNull(`fiscal_collection`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_collection`.`fdate`) <= parseDateTimeBestEffort(?))
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 102022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z
```

**对账注记（客观差异）**

- 两边均返回 9 个执收单位。
- Top1 金额一致：18,208,882,274.85 元。
- Top1 笔数不同：272（fid 去重）vs 253（paybook_count）。
- 时间轴不同：fill_date vs pay_date；cube 侧同编码多名称变体拼接展示。

### q07　测试云南省教育厅1直属下级单位合计缴款金额是多少？

**datus**（成功，110.1s）

**"测试云南省教育厅1"（单位编码 124）直属下级单位合计缴款金额：18,330,391,762.78 元（约 183.30 亿元）**

| 项目 | 数值 |
|---|---|
| 直属下级单位数 | **44 家**（全部有缴款记录） |
| 缴款笔数 | 693 笔（按 `uniqExact(fid)` 去重口径） |
| **合计缴款金额** | **18,330,391,762.78 元** |
| ├ 直缴（fbustype='1'） | 16,047,143,059.65 元（87.6%） |
| └ 汇缴（fbustype='2'） | 2,283,248,703.13 元（12.4%） |

上级单位本部自身无缴款记录。

**datus 生成 SQL**

```sql
SELECT
    count()                                        AS pay_rows,
    uniqExact(fid)                                 AS pay_cnt,
    round(SUM(famt), 2)                            AS total_amt,
    round(SUMIf(famt, fbustype = '1'), 2)          AS direct_amt,
    round(SUMIf(famt, fbustype = '2'), 2)          AS agg_amt
FROM yunnan0508.fne_paybook_full_high
WHERE fchgagenidcode IN (
    SELECT fagenidcode
    FROM (
        SELECT fagenidcode, fpidcode, fupdatetime,
               ROW_NUMBER() OVER (PARTITION BY fagenidcode ORDER BY fupdatetime DESC) AS _rn
        FROM yunnan0508.fab_agen
    ) t
    WHERE _rn = 1
      AND fpidcode = 'f8e06e9474514da29117a5194bbe503d'  -- 测试云南省教育厅1
)
```

**cube**（nomatch，52.4s）：nomatch——语义层成员面无单位层级成员，无法按"下级单位"作答

**对账注记（客观差异）**

- datus 通过源表 fab_agen.fpidcode 树形自联结实现：44 家下级、183.30 亿。
- cube 语义层无单位层级成员，直接报 nomatch。

### q08　各执收预算单位2022年的清分金额对比

**datus**（成功，108.8s）

| 排名 | 执收单位 | 笔数 | 清分金额（亿元） | 占比 | 缴款金额（亿元） | 清分率 |
|---|---|---|---|---|---|---|
| 1 | 测试云南测试环境 | 272 | 159.8653 | ≈100% | 182.0888 | 87.80% |
| 2 | 云南测试单位1209 | 4 | 0.0002 | <0.01% | 0.0002 | 100% |
| 3 | 测试云南医疗单位0729 | 19 | 0.0001 | <0.01% | 0.0001 | 100% |
| 3 | 测试1125 | 20 | 0.0001 | <0.01% | 0.0001 | 99.15% |
| 5 | 测试云南医疗单位0805 | 9 | ~0 | — | ~0 | 100% |
| 5 | 测试云南通用测试单位0720 | 13 | ~0 | — | ~0 | 100% |
| 5 | 测试云南通用Oracle0728 | 2 | ~0 | — | ~0 | 100% |
| 5 | 测试分成测试 | 9 | ~0 | — | 0.0001 | 49.02% |
| 5 | 测试测试单位0722 | 7 | ~0 | — | ~0 | 100% |
| **合计** | **9 个单位** | **355** | **≈159.866** | 100% | **≈182.09** | **≈87.8%** |

**datus 生成 SQL**

```sql
WITH
name_cnt AS (
    SELECT fchgagenidcode AS agen_code, trim(fchgagenname) AS agen_name, count() AS cnt
    FROM yunnan0508.fne_paybook_full_high
    WHERE toYear(toDate(ffilldate)) = 2022
    GROUP BY agen_code, agen_name
),
canon AS (
    SELECT agen_code, argMax(agen_name, cnt) AS agen_name
    FROM name_cnt
    GROUP BY agen_code
)
SELECT
    m.fchgagenidcode AS agen_code,
    any(c.agen_name) AS agen_name,
    count() AS rows,
    uniqExact(m.fid) AS bills,
    round(sum(m.fimamt) / 1e8, 4) AS clear_amt_yi,
    round(sum(m.famt) / 1e8, 4) AS pay_amt_yi,
    round(if(sum(m.famt) = 0, NULL, sum(m.fimamt) / sum(m.famt) * 100), 2) AS clear_rate_pct
FROM yunnan0508.fne_paybook_full_high m
INNER JOIN canon c ON m.fchgagenidcode = c.agen_code
WHERE toYear(toDate(m.ffilldate)) = 2022
GROUP BY m.fchgagenidcode
ORDER BY clear_amt_yi DESC
```

**cube**（answer，29.3s）

**口径：划出方执收单位 × 清分金额（划拨金额 trans_amt 降序，附分入金额 im_amt 与记录数）**（25 行）
| chg_agency_code | trans_amt | im_amt | count |
|---|---|---|---|
| 124045 | 63371 | 15986585353.85 | 291 |
| 001 | 5082 | 2541 | 16 |
| 124994 | 2966 | 28941171.61 | 141 |
| 125026 | 664.62 | 13384.84 | 36 |
| 124992 | 324 | 287174 | 8 |
| 124993 | 100 | 100 | 1 |
| 125020 |  | 1915.12 | 9 |
| 001001 |  | 0 | 2 |
| 124576 |  | 2057.68 | 13 |
| 425104 |  | 1601.32 | 6 |
| 125019 |  | 6864.26 | 19 |
| 124100 |  | 11663.68 | 19 |
| 124002 |  | 4964 | 17 |
| 125032 |  | 5500.66 | 22 |
| 125029 |  | 30 | 2 |
| 425002 |  | 24034.92 | 4 |
| 105015 |  | 0 | 2 |
| 427008 |  | 2158 | 2 |
| 127208 |  | 12448.24 | 22 |
| 124577 |  | 1377.76 | 7 |
| 425103 |  | 165008.58 | 43 |
| 124579 |  | 1100 | 2 |
| 125022 |  | 3803.64 | 20 |
| 998017 |  | 805.28 | 3 |
| 998015 |  | 4409.24 | 21 |

**cube 生成 SQL**

```sql
-- table[0] 口径：划出方执收单位 × 清分金额（划拨金额 trans_amt 降序，附分入金额 im_amt 与记录数）
SELECT `fiscal_allocation`.`fchgagencode` `fiscal_allocation_view__chg_agency_code`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation_view__trans_amt`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 时间范围不同：datus 限 2022 年 vs cube 全量（未加年份过滤）。
- 金额口径不同：datus 单一清分口径（fimamt）vs cube 划拨 trans_amt 与分入 im_amt 双口径并列。
- 主单位分入量级一致（159.87 亿级）；分组数不同（9 vs 25，随时间范围不同）。

### q09　哪些非叶子单位自己直接收了款？各收了多少？

**datus**（有SQL无最终答案，191.8s）

（无最终答案——多轮 SQL 后试图写临时文件被权限拒绝，会话中断）

**datus 生成 SQL**

（无）

**cube**（nomatch，22.5s）：nomatch——语义层无单位层级成员

**对账注记（客观差异）**

- datus 引擎运行中断（写文件权限拒绝），未产出最终答案。
- cube 报 nomatch（无单位层级成员）。

### q10　按执收单位统计未到账的缴款笔数

**datus**（成功，245.3s）

| 执收单位编码 | 执收单位名称 | 未到账缴款笔数 | 明细行数 |
|---|---|---|---|
| 124045 | 测试云南测试环境 | **1** | 1 |

**datus 生成 SQL**

```sql
SELECT
    fchgagencode                                        AS agen_code,
    arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS agen_name,
    uniqExact(fpaycode)                                 AS unpaid_book_cnt,
    count()                                             AS detail_rows
FROM yunnan0508.fne_paybook_full_high
WHERE fstate = '1'
  AND toDateOrNull(feffdate) < '2026-10-21'
GROUP BY fchgagencode
ORDER BY unpaid_book_cnt DESC
LIMIT 100
```

**cube**（ask→追问→answer，23.8s）

**欠缴笔数（待缴款+有效期已过期）× 执收单位**（1 行）
| chg_agency_code | chg_agency_name | paybook_count | count |
|---|---|---|---|
| 124045 | 001 / 测试云南测试环境 / 测试云南测试环境(试用版) / 测试云南测试环境(试用版)(试用版) | 1 | 1 |

**cube 生成 SQL**

```sql
-- table[0] 欠缴笔数（待缴款+有效期已过期）× 执收单位
SELECT `fiscal_collection`.`fchgagencode` `fiscal_collection_view__chg_agency_code`, `fiscal_collection`.chg_agency_name_canon `fiscal_collection_view__chg_agency_name`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count`, count(*) `fiscal_collection_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fstate` = ?) AND (toDateOrNull(`fiscal_collection`.`feffdate`) < parseDateTimeBestEffort(?))
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 10012026-10-21T00:00:00.000Z
```

**对账注记（客观差异）**

- 口径相同（有效 + 已过期），结果一致：1 笔，缴款书 124045。
- 笔数键表述不同：datus COUNT(DISTINCT fpaycode) vs cube paybook_count（缴款书）。

### q11　各预算科目清分金额排行，政府性基金收入103大类下哪些叶子科目收得最多？

**datus**（成功，191.7s）

| 排名 | 科目编码 | 科目名称 | 层级 | 清分金额（元） | 占比 | 清分笔数 |
|---|---|---|---|---|---|---|
| 1 | 103010201 | 中央农网还贷资金收入 | 4 | **15,985,889,302.18** | 99.81% | 412 |
| 2 | 1030110 | 民航发展基金收入 | 3 | 28,938,336.12 | 0.18% | 126 |
| 3 | 1030106 | 铁路建设基金收入 | 3 | 495,345.65 | <0.01% | 66 |
| 4 | 1030115 | 港口建设费收入 | 3 | 495,318.31 | <0.01% | 254 |
| 5 | 1030121 | 旅游发展基金收入 | 3 | 154,995.46 | <0.01% | 95 |
| 6 | 1030129 | 国家电影事业发展专项资金收入 | 3 | 36,668.96 | <0.01% | 23 |
| 7 | 1030146 | 国有土地收益基金收入 | 3 | 22,488.00 | <0.01% | 5 |
| 8 | 1030149 | 大中型水库移民后期扶持基金收入 | 3 | 60.00 | ~0 | 1 |
| 9 | 103014899 | 其他土地出让收入 | 4 | 33.00 | ~0 | 2 |

收得最多的是 103010201 中央农网还贷资金收入：159.86 亿元，占该大类 99.81%。

**datus 生成 SQL**

```sql
WITH subject_dim AS (
  SELECT fsubcode, fsubname, flevel, fpcode, fisleaf
  FROM (
    SELECT fsubcode, fsubname, fyear, flevel, fpcode, fisleaf,
           ROW_NUMBER() OVER (PARTITION BY fsubcode ORDER BY fyear DESC) AS _rn
    FROM yunnan0508.fab_subject
  ) WHERE _rn = 1
),
agg AS (
  SELECT fsubcode AS subject_code, SUM(fimamt) AS amt, uniqExact(fid) AS cnt
  FROM yunnan0508.fne_paybook_full_high
  GROUP BY subject_code
)
SELECT
  a.subject_code AS subject_code,
  s.fsubname AS subject_name,
  toString(s.flevel) AS subject_level,
  COALESCE(round(a.amt, 2), 0) AS clear_amount,
  a.cnt AS clear_cnt
FROM agg a
INNER JOIN subject_dim s ON a.subject_code = s.fsubcode
WHERE toString(s.fisleaf) = '1' AND startsWith(a.subject_code, '103') AND NOT startsWith(a.subject_code, '10301')
ORDER BY clear_amount DESC
```

**cube**（answer，30.2s）

**政府性基金收入（103）叶子科目清分金额排行（分入金额 im_amt，全量 20 科目）**（20 行）
| rec_sub_code | rec_sub_name | im_amt | count |
|---|---|---|---|
| 103010201 | 中央农网还贷资金收入 / 中央农网还贷资金收入25 / 普通话水平测试费 | 15985889302.18 | 275 |
| 1030110 | 民航发展基金收入 | 28938336.12 | 60 |
| 1030106 | 铁路建设基金收入 | 495345.65 | 44 |
| 1030115 | 港口建设费收入 | 495318.31 | 176 |
| 1030121 | 旅游发展基金收入 | 154995.46 | 49 |
| 1030129 | 国家电影事业发展专项资金收入 | 36668.96 | 16 |
| 1030146 | 国有土地收益基金收入 | 22488 | 4 |
| 103042762 | 考试考务费 | 17080 | 19 |
| 103042758 | 高等学校住宿费 | 16643 | 33 |
| 103042706 | 教师资格考试费 | 6531 | 3 |
| 103042755 | 中等职业学校学费 | 4513 | 11 |
| 103040702 | 考试考务费 | 680 | 14 |
| 103045754 | 教材费 | 580 | 9 |
| 103042707 | 普通话水平测试费 | 433 | 2 |
| 1030219 | 教育资金收入 | 260 | 7 |
| 1030801 | 国外捐赠收入 | 100 | 1 |
| 1030802 | 国内捐赠收入 | 100 | 1 |
| 1030149 | 大中型水库移民后期扶持基金收入 | 60 | 1 |
| 103014899 | 其他土地出让收入 | 33 | 1 |
| 103042751 | 预防接种劳务费 | 0 | 2 |

**cube 生成 SQL**

```sql
-- table[0] 政府性基金收入（103）叶子科目清分金额排行（分入金额 im_amt，全量 20 科目）
SELECT `fiscal_allocation`.`frecsubcode` `fiscal_allocation_view__rec_sub_code`, `fiscal_allocation`.rec_sub_name_canon `fiscal_allocation_view__rec_sub_name`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
WHERE ((`fiscal_allocation`.`frecsubcode` ILIKE ?|| '%'))
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 500103
```

**对账注记（客观差异）**

- 头部分类数字一致：103010201 = 15,985,889,302.18（99.81%）。
- 叶子判定方法不同：datus 取 fab_subject 的 fisleaf 标志 vs cube 按 '103' 前缀聚合后声明 20 个编码两两无前缀包含。
- datus 先做 103→10301 层级修正再作答；cube 直接按 '103' 前缀聚合。

### q12　民航发展基金历年缴款金额趋势

**datus**（成功，878.4s）

| 年份 | 笔数 | 缴款金额(万元) | 其中实缴(万元) | 趋势 |
|------|-----:|-------------:|-------------:|------|
| 2022 | 4 | 0.05 | — | 起步 |
| 2023 | 84 | 0.78 | 0.29 | 平稳低位 |
| 2024 | 261 | **2,912.22** | 2,898.67 | ⬆ 峰值（实缴率 99.5%） |
| 2025 | 269 | 246.09 | 187.75 | ⬇ 大幅回落（-91.6%） |
| 2026 | 199 | 15.57 | 4.25 | ⬇ 持续走低 |
| 2027 | 234 | 60.71 | 19.36 | ⬆ 回升 |
| 2028 | 17 | 0.83 | 0.23 | ⬇ |
| 2029 | 8 | 0.23 | — | 边缘 |

**datus 生成 SQL**

```sql
SELECT
  toYear(toDate(feffdate)) AS y,
  count() AS rows_cnt,
  round(sum(famt)/10000, 2) AS amt_wan,
  round(sumIf(famt, fstate='3')/10000, 2) AS paid_wan,
  uniqExact(fpaycode) AS pay_cnt
FROM yunnan0508.une_paybook_high
WHERE fitemcode = '1030110001'
GROUP BY y
ORDER BY y
```

**cube**（answer，71.5s）

**民航发展基金收入（项目 1030110001）历年缴款趋势（按缴款日期 pay_date 年度，金额=amt）**（5 行）
| year | amt | paybook_count |
|---|---|---|
| 2022-01-01T00:00:00.000 | 27879.00 | 3 |
| 2023-01-01T00:00:00.000 | 1403.30 | 7 |
| 2024-01-01T00:00:00.000 | 28962042.04 | 68 |
| 2025-01-01T00:00:00.000 | 1837652.80 | 37 |
| 2026-01-01T00:00:00.000 | 21801.94 | 11 |

**cube 生成 SQL**

```sql
-- table[0] 民航发展基金收入（项目 1030110001）历年缴款趋势（按缴款日期 pay_date 年度，金额=amt）
SELECT toDateTime64(toStartOfYear(toTimeZone(toDateTime64(toDateOrNull(`fiscal_collection`.`fdate`), 0), 'UTC'), 'UTC'), 0, 'UTC') `fiscal_collection_view__pay_date_year`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fitemcode` = ?)
GROUP BY 1
ORDER BY  1  ASC
LIMIT 1001030110001
```

**对账注记（客观差异）**

- 数据源表不同：une_paybook_high（全口径）vs fne_paybook_full_high（fne 直缴链）。
- 时间轴不同：feffdate（生效日）vs pay_date（缴款日）。
- 合计不同：约 3,236 万 vs 3,085.09 万（差约 151 万）。
- datus 覆盖 2027-2029 未来年份（数据噪声），cube 无。

### q13　按收入分类统计缴款金额：政府性基金收入、专项收入、行政事业性收费收入、罚没收入各占多少？

**datus**（成功，89.9s）

| 收入分类 | 缴款金额（亿元） | 金额占比 | 笔数（去重 fid） |
|---|---:|---:|---:|
| **政府性基金收入** | 182.85 | **99.74%** | 857 |
| **专项收入** | 0.31 | 0.17% | 133 |
| **行政事业性收费收入** | 0.16 | 0.09% | 96 |
| **罚没收入** | 0.000003（仅 300 元） | ≈0 | 9 |
| 未分类（fincomesortname 为空） | 0.000006（600 元） | ≈0 | 6 |
| **合计** | **183.22** | 100% | 1,101 |

**datus 生成 SQL**

```sql
SELECT
    if(fincomesortname = '', '未分类', fincomesortname) AS income_category,
    round(SUM(famt) / 10000, 2)        AS amt_wan_yuan,
    round(SUM(famt) * 100 / SUM(SUM(famt)) OVER (), 4) AS amt_pct,
    uniqExact(fid)                     AS pay_cnt_fid
FROM fne_paybook_full_high
GROUP BY income_category
ORDER BY amt_wan_yuan DESC
```

**cube**（error(502)→日志恢复，?s）

**收入类别×缴款金额及占比（全量）**（5 行）
| income_sort_name | amt | share_pct |
|---|---|---|
| 政府性基金收入 | 18285222472.21 | 99.7437 |
| 专项收入 | 30951894.082 | 0.1688 |
| 行政事业性收费收入 | 16031930.84 | 0.0874 |
| （空） | 600 | 0.0000033 |
| 罚没收入 | 306 | 0.0000017 |

**cube 生成 SQL**

```sql
-- table[0] 收入类别×缴款金额及占比（全量）
SELECT `fiscal_collection`.`fincomesortname` `fiscal_collection_view__income_sort_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 各分类数字一致：政府性基金、专项、行政事业性收费、罚没、未分类（元级或接近元级）。
- datus 答案文本"合计 183.22 亿"与其自身分项之和（≈183.32 亿）不勾稽；cube 分母 18,332,207,203.13 元。
- datus 另计 1,101 笔（fid 去重）；cube 未计笔数。

### q14　按资金性质分组统计缴款金额

**datus**（成功，150.4s）

| 资金性质码 | 资金性质 | 缴款金额（元） | 行数 | 金额占比 |
|---|---|---:|---:|---:|
| 12 | 政府性基金预算收入 | 18,316,046,350.64 | 1,083 | ≈99.9% |
| 2 | 财政专户管理资金 | 14,867,151.04 | 86 | ≈0.08% |
| 11 | 一般公共预算收入 | 1,293,101.45 | 97 | ≈0.007% |
| 5 | 其他 | 600.00 | 6 | ≈0.000003% |
| **合计** | | **18,332,214,203.13** | **1,272** | 100% |

**datus 生成 SQL**

```sql
SELECT
    ffundsnaturecode AS funds_nature_code,
    ffundsnaturename AS funds_nature_name,
    count()           AS row_count,
    round(sum(famt), 2) AS pay_amt
FROM yunnan0508.fne_paybook_full_high
GROUP BY ffundsnaturecode, ffundsnaturename
ORDER BY pay_amt DESC
```

**cube**（answer，26.9s）

**收入侧资金性质×缴款金额（全量，无时间过滤）**（5 行）
| rec_funds_nature_code | rec_funds_nature_name | amt | count |
|---|---|---|---|
| 12 | 政府性基金预算收入 | 16016379742.39 | 589 |
|  | （未标注资金性质） | 2314603154.582 | 544 |
| 11 | 一般公共预算收入 | 1184377.16 | 63 |
| 2 | 财政专户管理资金 | 39329 | 70 |
| 5 | 其他 | 600 | 6 |

**cube 生成 SQL**

```sql
-- table[0] 收入侧资金性质×缴款金额（全量，无时间过滤）
SELECT `fiscal_collection`.`frecfundsnaturecode` `fiscal_collection_view__rec_funds_nature_code`, `fiscal_collection`.`frecfundsnaturename` `fiscal_collection_view__rec_funds_nature_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, count(*) `fiscal_collection_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 取的字段不同：缴款票面 ffundsnaturecode vs 收入归属 rec_funds_nature_code。
- 数字完全不同（最大组 18,316,046,350.64 vs 16,016,379,742.39）。
- cube 存在 544 行空编码组（2,314,603,154.58 元）；datus 无空码组。

### q15　缴款金额前5的收费项目，按直缴汇缴拆分展示

**datus**（成功，120.6s）

| 排名 | 收费项目 | 项目ID | 缴款金额合计(元) | 直缴金额(元) | 直缴占比 | 汇缴金额(元) | 汇缴占比 | 直缴笔数 | 汇缴笔数 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 农网还贷资金收入 | 530020000079 | 16,044,829,547.49 | 16,014,461,111.69 | 99.81% | 30,368,435.80 | 0.19% | 272 | 25 |
| 2 | 国有重点煤炭企业生产用电、核工业铀扩散厂和堆化工厂生产用电农网还贷资金 | 530020000081 | 2,238,164,885.91 | 159,670.01 | 0.01% | 2,238,005,215.90 | 99.99% | 53 | 14 |
| 3 | 民航发展基金收入 | 530020000503 | 30,850,779.08 | 30,758,057.70 | 99.70% | 92,721.38 | 0.30% | 87 | 39 |
| 4 | 高等学校住宿费 | 530020000028 | 14,841,170.00 | 19,271.00 | 0.13% | 14,821,899.00 | 99.87% | 35 | 5 |
| 5 | 公办幼儿园保教费 | 530020000823 | 1,156,320.00 | 0.00(无直缴) | — | 1,156,320.00 | 100% | 0 | 1 |

**datus 生成 SQL**

```sql
WITH
top5 AS (
    SELECT fitemidcode FROM fne_paybook_full_high
    GROUP BY fitemidcode ORDER BY SUM(famt) DESC LIMIT 5
),
names AS (
    SELECT fitemidcode AS item_id,
           argMax(fitemname, ffilldate) AS item_name,
           groupUniqArray(fitemname) AS all_names
    FROM fne_paybook_full_high
    WHERE fitemidcode IN top5
    GROUP BY item_id
),
bus AS (
    SELECT fitemidcode AS item_id, fbustype AS bustype,
           SUM(famt) AS amt, uniqExact(fid) AS cnt_fid
    FROM fne_paybook_full_high
    WHERE fitemidcode IN top5
    GROUP BY item_id, bustype
)
SELECT n.item_id, n.item_name, n.all_names,
       round(SUM(b.amt), 2) AS amt_total,
       round(sumIf(b.amt, b.bustype = '1'), 2) AS amt_direct,
       round(sumIf(b.amt, b.bustype = '2'), 2) AS amt_agg,
       sumIf(b.cnt_fid, b.bustype = '1') AS cnt_direct,
       sumIf(b.cnt_fid, b.bustype = '2') AS cnt_agg
FROM bus b INNER JOIN names n ON b.item_id = n.item_id
GROUP BY n.item_id, n.item_name, n.all_names
ORDER BY amt_total DESC
```

**cube**（answer，26.1s）

**口径A：前5收费项目按业务类型（直缴/汇缴）拆分**（10 行）
| item_code | item_name | bus_type | amt |
|---|---|---|---|
| 103010201001 | 农网还贷资金收入 | 1 | 15985880682.69 |
| 103010201002 | 国有重点煤炭企业生产用电、核工业铀扩散厂和堆化工厂生产用电农网还贷资金 | 2 | 2238005215.90 |
| 1030110001 | 民航发展基金收入 | 1 | 30758057.70 |
| 103010201001 | 农网还贷资金收入 | 2 | 30297369.11 |
| 1030102010011 | 农网还贷资金收入a | 1 | 28580429.00 |
| 103042758 | 高等学校住宿费 | 2 | 14821899.00 |
| 103010201002 | 国有重点煤炭企业生产用电、核工业铀扩散厂和堆化工厂生产用电农网还贷资金 | 1 | 159670.01 |
| 1030110001 | 民航发展基金收入 | 2 | 92721.38 |
| 1030102010011 | 农网还贷资金收入a | 2 | 71066.69 |
| 103042758 | 高等学校住宿费 | 1 | 19271.00 |

**cube 生成 SQL**

```sql
-- table[0] 口径A：前5收费项目按业务类型（直缴/汇缴）拆分
SELECT `fiscal_collection`.`fitemcode` `fiscal_collection_view__item_code`, `fiscal_collection`.item_name_canon `fiscal_collection_view__item_name`, `fiscal_collection`.`fbustype` `fiscal_collection_view__bus_type`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fitemcode` IN (?, ?, ?, ?, ?))
GROUP BY 1, 2, 3
ORDER BY  4  DESC
LIMIT 10010301020100110301020100210301100011030102010011103042758
```

**对账注记（客观差异）**

- 项目主键体系不同：fitemidcode（530020000xxx）vs item_code（10301xxxxxx），Top5 集合不同（datus 含保教费，cube 含"农网还贷 a"变体编码）。
- 名称变体处理不同：datus 按 ID 归并 vs cube 按编码分组、变体分列。
- bus_type 映射表述不同：datus 断言 1=直缴/2=汇缴；cube 声明元数据无该映射、按编码原样展示。
- 民航项目金额量级一致：3,085.08 万 vs 3,085.09 万。

### q16　按归属区划统计清分金额

**datus**（成功，84.3s）

| 归属区划代码 | 区划名称 | 明细行数 | 清分金额（元） |
|---|---|---:|---:|
| 530000 | 云南省本级 | 686 | 16,016,072,677.53 |
| 000000 | 中央 | 31 | 4,516.12 |
| 530100 | 昆明市本级 | 8 | 1,778.70 |
| 530102 | 五华区 | 1 | 495.33 |
| 532929 | 云龙县 | 2 | 0.00 |
| （空） | 未填归属区划 | 544 | 0.00（fimamt 全 NULL） |

合计 1,272 行，清分金额总计 160.16 亿元，几乎全部集中在云南省本级（530000）。

**datus 生成 SQL**

```sql
SELECT
    if(frecrgncode = '', '(未填)', frecrgncode) AS frecrgncode,
    any(frecrgnname)                            AS frecrgnname,
    count()                                     AS rows_cnt,
    COALESCE(sum(fimamt), 0)                    AS clear_amt
FROM yunnan0508.fne_paybook_full_high
GROUP BY frecrgncode
ORDER BY clear_amt DESC
```

**cube**（answer，31.5s）

**清分金额（分入金额 im_amt）×收入归属区划**（5 行）
| rec_rgn_code | im_amt | count |
|---|---|---|
| 530000 | 16016072677.53 | 686 |
| 000000 | 4516.12 | 31 |
| 530100 | 1778.7 | 8 |
| 530102 | 495.33 | 1 |
| 532929 | 0 | 2 |

**cube 生成 SQL**

```sql
-- table[0] 清分金额（分入金额 im_amt）×收入归属区划
SELECT `fiscal_allocation`.`frecrgncode` `fiscal_allocation_view__rec_rgn_code`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 五组金额与行数分毫不差（16,016,072,677.53/686、4,516.12、1,778.70、495.33、0）。
- 空编码组：datus 报 544 行 fimamt 全 NULL（不进聚合），cube 未单列空组。

### q17　按执收区划名称统计缴款金额

**datus**（成功，88.5s）

| 执收区划名称 | 缴款金额（元） | 缴款笔数（去重 fid） | 笔均金额（元） |
|---|---:|---:|---:|
| 云南省本级 | 18,330,965,893.01 | 1,081 | 16,957,415.26 |
| 云龙县 | 1,156,320.00 | 1 | 1,156,320.00 |
| 五华区 | 79,406.12 | 6 | 13,234.35 |
| 昆明市本级 | 5,184.00 | 9 | 576.00 |
| 官渡区 | 400.00 | 4 | 100.00 |
| **合计** | **18,332,205,003.13** | **1,101** | — |

**datus 生成 SQL**

```sql
SELECT
    fchgrgnname AS collect_region_name,
    ROUND(SUM(famt), 2) AS pay_amt,
    uniqExact(fid) AS pay_cnt,
    ROUND(SUM(famt) / uniqExact(fid), 2) AS avg_amt
FROM yunnan0508.fne_paybook_full_high
GROUP BY fchgrgnname
ORDER BY pay_amt DESC
```

**cube**（answer，39.0s）

**缴款金额按执收区划（rec_rgn_code+名称展示，全期）**（6 行）
| rec_rgn_code | rec_rgn_name | amt | count |
|---|---|---|---|
| 530000 | 云南省本级 | 16016434579.21 | 686 |
|  |  | 2314603154.58 | 544 |
| 532929 | 云龙县 | 1156320 | 2 |
| 000000 | 中央 | 9617.68 | 31 |
| 530100 | 昆明市本级 | 2541 | 8 |
| 530102 | 五华区 | 990.66 | 1 |

**cube 生成 SQL**

```sql
-- table[0] 缴款金额按执收区划（rec_rgn_code+名称展示，全期）
SELECT `fiscal_collection`.`frecrgncode` `fiscal_collection_view__rec_rgn_code`, `fiscal_collection`.rec_rgn_name_canon `fiscal_collection_view__rec_rgn_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, count(*) `fiscal_collection_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 分组字段不同：datus fchgrgn*（执收区划）vs cube rec_rgn*（收入区划）——题目问"执收区划"。
- 数字完全不同（datus 主组 183.31 亿 vs cube 省本级 160.16 亿 + 空 23.15 亿）。
- datus 出现官渡区组；cube 出现中央组与空组。

### q18　五华区的执收单位有哪些、各收了多少钱？

**datus**（成功，98.3s）

| 执收单位 | 缴款笔数 | 缴款金额（元） |
|---|---:|---:|
| 智能核销五华区测试单位开票点 | 4 | 77,324.80 |
| 李思维 | 1 | 1,981.32 |
| 开票点001 | 1 | 100.00 |
| **合计** | **6** | **79,406.12** |

对照口径：按资金归属五华区（frecrgnname）统计仅李思维 1 笔 / 990.66 元。

**datus 生成 SQL**

```sql
SELECT
    fchgrgnname AS agen_rgn,
    count() AS row_cnt,
    uniqExact(fid) AS bill_cnt,
    round(sum(famt), 2) AS amt
FROM fne_paybook_full_high
GROUP BY fchgrgnname
ORDER BY amt DESC
```

**cube**（answer，34.4s）

**五华区（530102）执收单位×缴款金额（缴款侧 amt）**（3 行）
| chg_agency_code | chg_agency_name | amt | paybook_count |
|---|---|---|---|
| 777001 | 智能核销五华区测试单位开票点 | 77324.80 | 2 |
| 125026 | 云南医保测试单位改名 / 开票点一 / 李思维 | 1981.32 | 1 |
| 124994 | 云南发展改革委员会 / 开票点001 / 开票点002 | 100.00 | 1 |

**cube 生成 SQL**

```sql
-- table[0] 五华区（530102）执收单位×缴款金额（缴款侧 amt）
SELECT `fiscal_collection`.`fchgagencode` `fiscal_collection_view__chg_agency_code`, `fiscal_collection`.chg_agency_name_canon `fiscal_collection_view__chg_agency_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fchgrgncode` = ?)
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 100530102
```

**对账注记（客观差异）**

- 金额与单位一致：3 家、合计 79,406.12 元、最大 77,324.80。
- 笔数不同：6（fid 去重）vs 4（paybook_count）。
- datus 另给执收/收入两口径对照（收入口径 990.66）；cube 单口径。

### q19　各收款银行2022年各收了多少笔、多少钱？

**datus**（成功，75.4s）

| 收款银行 | 笔数 | 金额（元） | 金额（亿元） |
|---|---:|---:|---:|
| 中国建设银行 | 226 | 18,208,121,939.04 | ≈182.08 |
| 中国银行 | 107 | 800,419.02 | ≈80.04 万 |
| 中国邮政储蓄银行 | 7 | 7,778.00 | 0.78 万 |
| 中国工商银行 | 11 | 5,426.21 | 0.54 万 |
| 中国农业银行 | 3 | 510.00 | 510 元 |
| 中国光大银行 | 1 | 500.00 | 500 元 |
| **合计** | **355** | **18,208,936,572.27** | **≈182.09 亿** |

**datus 生成 SQL**

```sql
SELECT
    trim(frecbankname) AS bank_name,
    uniqExact(fid)             AS bill_cnt,
    round(sum(famt), 2)        AS total_amt
FROM fne_paybook_full_high
WHERE toYear(toDate(ffilldate)) = 2022
GROUP BY bank_name
ORDER BY total_amt DESC
```

**cube**（answer，22.4s）

**2022 年各收款银行：缴款笔数与金额（缴款日期口径）**（6 行）
| rec_bank_code | rec_bank_name | paybook_count | amt |
|---|---|---|---|
| 0105 | 中国建设银行 | 211 | 18208121939.04 |
| 0104 | 中国银行 | 103 | 800419.02 |
| 0100 | 中国邮政储蓄银行 | 7 | 7778 |
| 0102 | 中国工商银行 | 9 | 5426.21 |
| 0103 | 中国农业银行 | 3 | 510 |
| 0303 | 中国光大银行 | 1 | 500 |

**cube 生成 SQL**

```sql
-- table[0] 2022 年各收款银行：缴款笔数与金额（缴款日期口径）
SELECT `fiscal_collection`.`frecbankcode` `fiscal_collection_view__rec_bank_code`, `fiscal_collection`.`frecbankname` `fiscal_collection_view__rec_bank_name`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (toDateOrNull(`fiscal_collection`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_collection`.`fdate`) <= parseDateTimeBestEffort(?))
GROUP BY 1, 2
ORDER BY  4  DESC
LIMIT 1002022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z
```

**对账注记（客观差异）**

- 银行家数一致（6）。
- 建行金额量级一致（182.08 亿级）。
- 笔数与分布不同：总笔数 355 vs 334、建行 226 vs 211（时间轴 fill_date vs pay_date、笔数键 fid vs paybook_count）。
- 分组键不同：datus 银行名称（trim 后）vs cube 银行编码。

### q20　归属区划在云南省本级以外的缴款金额有多少？

**datus**（成功，151.3s）

| 口径 | 金额（元） | 笔数 |
|---|---|---|
| **省本级以外（区划有明确值）** | **1,169,469.34（约 116.9 万）** | 41 笔 |
| 归属区划为空（未落值） | 2,314,603,154.58（约 23.15 亿） | 544 笔 |
| 合计（含空串宽口径） | 2,315,772,623.92（约 23.16 亿） | 585 笔 |

明确非省本级的 41 笔构成：云龙县 1,156,320.00/1、中央 9,617.68/31、昆明市本级 2,541.00/8、五华区 990.66/1；对比云南省本级 16,016,434,579.21 元（554 笔）。

**datus 生成 SQL**

```sql
SELECT
    round(sumIf(famt, frecrgnname = '云南省本级'), 2)                        AS prov_amt,
    round(sumIf(famt, frecrgnname != '云南省本级'), 2)                       AS non_prov_amt_incl_blank,
    uniqExactIf(fid, frecrgnname != '云南省本级')                            AS non_prov_bill_cnt,
    round(sumIf(famt, frecrgnname != '云南省本级' AND frecrgnname != ''), 2) AS non_prov_amt_named,
    round(sumIf(famt, frecrgnname = ''), 2)                                  AS blank_amt
FROM fne_paybook_full_high
```

**cube**（answer，31.8s）

**云南省本级以外缴款合计（rec_rgn_code≠530000）**（1 行）
| amt | paybook_count |
|---|---|
| 2315772623.922 | 504 |

**口径参照：按收入归属区划分组（全部）**（6 行）
| rec_rgn_code | rec_rgn_name | amt | paybook_count |
|---|---|---|---|
| 530000 | 云南省本级 | 16016434579.21 | 507 |
|  |  | 2314603154.582 | 465 |
| 532929 | 云龙县 | 1156320 | 1 |
| 000000 | 中央 | 9617.68 | 29 |
| 530100 | 昆明市本级 | 2541 | 8 |
| 530102 | 五华区 | 990.66 | 1 |

**cube 生成 SQL**

```sql
-- table[0] 云南省本级以外缴款合计（rec_rgn_code≠530000）
SELECT sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`frecrgncode` <> ? OR `fiscal_collection`.`frecrgncode` IS NULL)
LIMIT 10530000

-- table[1] 口径参照：按收入归属区划分组（全部）
SELECT `fiscal_collection`.`frecrgncode` `fiscal_collection_view__rec_rgn_code`, `fiscal_collection`.rec_rgn_name_canon `fiscal_collection_view__rec_rgn_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
GROUP BY 1, 2
ORDER BY  3  DESC
LIMIT 200
```

**对账注记（客观差异）**

- 金额完全一致：含空 2,315,772,623.92、剔除空 1,169,469.34。
- 笔数不同：41/585（fid 去重）vs 39/504（paybook_count）。
- 实现方式不同：datus 按名称列分组后取非省本级档 vs cube 编码不等于过滤（空组自然落入"≠530000"）。

### q21　已划拨和未划拨的金额各是多少？

**datus**（成功，188.0s）

**已划拨 21,024.00 元（34 个批次），未划拨 38,142.30 元（87 个批次）**，合计 59,166.30 元。

| 划拨状态 | 批次数 | 划拨金额（元） |
|---|---:|---:|
| 已划拨（fistransfer='1'） | 34 | 21,024.00 |
| 未划拨（fistransfer='0'） | 87 | 38,142.30 |
| **合计** | **121** | **59,166.30** |

**datus 生成 SQL**

```sql
SELECT
  multiIf(istransfer_grp = '1', '已划拨', '未划拨') AS status,
  uniqExact(fcollectid) AS batches,
  round(sum(batch_amt), 2) AS amount
FROM (
  SELECT
    fcollectid,
    max(fistransfer) AS istransfer_grp,
    max(ftransamt) AS batch_amt
  FROM fne_funddivide_transfer
  WHERE fistransfer IN ('0', '1') AND ftransamt IS NOT NULL
  GROUP BY fcollectid
)
GROUP BY istransfer_grp
ORDER BY istransfer_grp
```

**cube**（answer，47.8s）

**划拨口径：已划拨 vs 未划拨（清分收入总额拆分）**（1 行）
| trans_amt | im_amt | im_amt_not_transferred | trans_amt_rate |
|---|---|---|---|
| 72507.62 | 16016079467.68 | 16016006960.06 | 0.0005 |

**cube 生成 SQL**

```sql
-- table[0] 划拨口径：已划拨 vs 未划拨（清分收入总额拆分）
SELECT sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation_view__trans_amt`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
LIMIT 10
```

**对账注记（客观差异）**

- 主语不同：datus 限有划拨记录的 121 个批次 vs cube 全量清分记录。
- 金额不同：datus 去重后 59,166.30 vs cube trans_amt 直 SUM 72,507.62（恰为 datus 指出的"未去重虚增"量级）。
- 状态判据不同：datus 用 fistransfer 字段 vs cube is_transfer 实测全空、改按金额差值推算。

### q22　缴库报文里已确认入库和待国库确认的金额各是多少？

**datus**（成功，91.6s）

| 缴库状态 | 入库确认状态 | 笔数（fid） | 金额（元） |
|---|---|---:|---:|
| **已缴库 + 已确认入库** | `fstatus='9'` & `fincomestatus='1'` | **23** | **11,064.00** |
| **已缴库 + 待国库确认** | `fstatus='9'` & `fincomestatus='0'` | **3** | **35,240.09** |

其余 50 笔（29,488,802.05 元）为 `fstatus='0'` 的未缴库报文，未计入。

**datus 生成 SQL**

```sql
SELECT
    fstatus AS jiaoku_status,
    toString(fincomestatus) AS income_status,
    uniqExact(fid) AS fid_cnt,
    round(SUM(ftotalamt), 2) AS total_amt
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY fid) AS _rn
    FROM yunnan0508.fne_treasury_transfer_new
)
WHERE _rn = 1
GROUP BY fstatus, income_status
ORDER BY jiaoku_status, income_status
```

**cube**（answer，23.0s）

**缴库报文：已确认入库 vs 待国库确认（enter_status 分组，全量）**（2 行）
| enter_status | amt | count | bill_count |
|---|---|---|---|
| 0（待国库确认/未入库） | 29409625.05 | 50 | 44 |
| 1（已确认入库/已入国库） | 46304.09 | 26 | 26 |

**cube 生成 SQL**

```sql
-- table[0] 缴库报文：已确认入库 vs 待国库确认（enter_status 分组，全量）
SELECT `fiscal_treasury`.`fenterstatus` `fiscal_treasury_view__enter_status`, sum(`fiscal_treasury`.`famt`) `fiscal_treasury_view__amt`, count(*) `fiscal_treasury_view__count`, COUNT(DISTINCT `fiscal_treasury`.`ftransno`) `fiscal_treasury_view__bill_count` 
FROM  (SELECT * FROM (
  SELECT fid,
         any(fpid) AS fpid, any(ftransno) AS ftransno,
         any(fsubcode) AS fsubcode, any(fsubname) AS fsubname,
         any(fsublevel) AS fsublevel, any(fsublevelname) AS fsublevelname,
         any(fstatus) AS fstatus, any(fenterstatus) AS fenterstatus,
         any(freconcilestatus) AS freconcilestatus, any(fsharerate) AS fsharerate,
         any(fchgrgncode) AS fchgrgncode, any(frecrgncode) AS frecrgncode,
         any(fchgagencode) AS fchgagencode,
         any(fpayacctname) AS fpayacctname, any(frecacctname) AS frecacctname,
         any(fdate) AS fdate, any(fenterdate) AS fenterdate,
         any(freconciledate) AS freconciledate,
         any(famt) AS famt, any(ftotalamt) AS ftotalamt
  FROM fne_treasury_transfer_new
  GROUP BY fid
) t
LEFT JOIN (SELECT fsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
           FROM fne_treasury_transfer_new WHERE fsubcode != '' GROUP BY fsubcode) s
ON t.fsubcode = s.fsubcode
)  AS `fiscal_treasury`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 状态字段不同：datus fstatus + fincomestatus 双字段组合 vs cube enter_status 单字段。
- 组划分不同：datus 只计已缴库两组、另列未缴库 vs cube 二分全部。
- 数字不同：已入库 11,064.00 vs 46,304.09；未入库/未缴库 29,488,802.05 vs 29,409,625.05。

### q23　汇总批次一共多少个？

**datus**（成功，94.6s）

| 口径 | 数量 |
|---|---|
| **有效汇总批次（`fcollectid != ''` 去重）** | **428 个** |
| 其中：有批次头行的批次（`fid = fcollectid`） | 425 个 |
| 其中：仅有明细行、无头行的批次 | 3 个 |
| 未汇总入批次的清分明细行（`fcollectid = ''`，共 178 行） | 不计为批次 |
| 若把空串也算一个"值" | 429（无效口径，不建议） |

**datus 生成 SQL**

```sql
SELECT
  count()                                        AS total_rows,
  uniqExactIf(fcollectid, fcollectid != '')      AS batches_nonempty,
  countIf(fcollectid = '')                       AS rows_empty_key,
  countIf(fcollectid != '' AND fid = fcollectid) AS header_rows
FROM yunnan0508.fne_funddivide_transfer
```

**cube**（ask→追问→answer，21.5s）

**口径A：汇总批次（collect_flag=1）清分记录数**（1 行）
| count |
|---|
| 550 |

**cube 生成 SQL**

```sql
-- table[0] 口径A：汇总批次（collect_flag=1）清分记录数
SELECT count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
WHERE (if(empty(`fiscal_allocation`.`fcollectid`), '0', '1') = ?)
ORDER BY  1  DESC
LIMIT 1001
```

**对账注记（客观差异）**

- 计数对象不同：datus 按键去重的批次数（428）vs cube collect_flag=1 的记录行数（550）。
- datus 同时报出非空键明细 550 行对应 428 个批次——与 cube 的 550 是同一行数口径的不同计数对象。
- 实现路径不同：datus 直查源表 uniqExact vs cube 视图成员（collect_flag）。

### q24　未清分的缴款笔数和金额是多少？

**datus**（成功，79.5s）

| 指标 | 数值 |
|---|---|
| **未清分缴款笔数** | **515 笔**（按 `fid` 去重口径） |
| **未清分缴款金额** | **2,314,588,645.58 元**（约 **23.15 亿元**） |

**datus 生成 SQL**

```sql
SELECT
    COUNT(DISTINCT fid) AS cnt_uncleared,
    ROUND(SUM(famt), 2) AS amt_uncleared
FROM yunnan0508.fne_paybook_full_high
WHERE fisclear = '0'
```

**cube**（answer，30.8s）

**未清分缴款（clear_date 为空）笔数与金额**（1 行）
| paybook_count | amt |
|---|---|
| 439 | 2314587534.582 |

**cube 生成 SQL**

```sql
-- table[0] 未清分缴款（clear_date 为空）笔数与金额
SELECT COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (toDateOrNull(`fiscal_collection`.`fcleardate`) IS NULL)
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- 金额几乎一致：差 1,111.00 元。
- 过滤判据不同：datus fisclear 标志位 vs cube clear_date 空判（cube 声明模型无 is_cleared 成员）。
- 笔数不同：515（fid 去重）vs 439（paybook_count）。

### q25　清分率按业务类型分组对比：直缴和汇缴各是多少？

**datus**（成功，89.9s）

| 业务类型 | 明细行数 | 缴款笔数 | 非税缴款金额（元） | 清分金额（元） | 清分率 |
|---|---|---|---|---|---|
| **直缴**（fbustype='1'） | 1,063 | 848 | 160.47 亿 | 160.16 亿 | **99.80%** |
| **汇缴**（fbustype='2'） | 209 | 120 | 22.85 亿 | 8.02 万 | **≈0.00%**（实际 0.0035%） |
| 整体（全类型，对照） | 1,272 | 968 | 183.32 亿 | 160.16 亿 | 87.37% |

**datus 生成 SQL**

```sql
SELECT
    multiIf(fbustype = '1', '直缴', fbustype = '2', '汇缴', concat('其他:', fbustype)) AS bustype_name,
    count() AS detail_rows,
    uniqExact(fpaycode) AS pay_count,
    round(SUM(famt), 2) AS non_tax_amt,
    round(SUM(fimamt), 2) AS clear_amt,
    round(SUM(fimamt) / SUM(famt) * 100, 2) AS clear_rate_pct
FROM yunnan0508.fne_paybook_full_high
GROUP BY fbustype
ORDER BY fbustype
```

**cube**（ask→追问→answer，33.6s）

**清分率（口径：划转成功笔数÷清分记录数，fiscal_allocation_view）**（2 行）
| count | trans_stats | clear_rate_num | clear_rate_pct |
|---|---|---|---|
| 728 | 全部 | 0 | 0.00 |
| 0 | 9 | 0 | 0.00 |

**业务类型分布（缴款全景，bus_type：1=直缴 2=汇缴，参考背景）**（2 行）
| bus_type | paybook_count | count |
|---|---|---|
| 1 | 848 | 1063 |
| 2 | 120 | 209 |

**cube 生成 SQL**

```sql
-- table[0] 清分率（口径：划转成功笔数÷清分记录数，fiscal_allocation_view）
SELECT count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
ORDER BY  1  DESC
LIMIT 100

-- table[1] 业务类型分布（缴款全景，bus_type：1=直缴 2=汇缴，参考背景）
SELECT `fiscal_collection`.`fbustype` `fiscal_collection_view__bus_type`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count`, count(*) `fiscal_collection_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

**对账注记（客观差异）**

- datus 分子分母同在 fne_paybook_full_high（fimamt/famt 组内比值），给出三个比值；cube 分子分母分属两视图、声明无 join path，改给拍板口径与参考分布。
- cube 参考分布的行数与 datus 一致：直缴 1,063 行、汇缴 209 行。
- cube 拍板口径比值 0.00% 与 datus 汇缴比值 ≈0.0035% 量级接近，但两者分母定义不同。

## 三、cube 独有验证题（q26-q30）

> q26-q30 来自 08 文件"还答不了的"nomatch 验证题，datus 链路未测；列于此供完整性核对。

### q26　划拨金额按划入的下级区划和划入单位拆分统计

- 判定：answer（30.3s）
- 摘要：近似作答：「下级区划/下级单位」无层级成员，按划入方区划（rec_rgn_code）× 划入方单位编码（rec_agency_code，无名称列）替代并已声明，结果含全部区划层级。

**划拨金额：划入区划×划入单位（清分流向）**（9 行）
| rec_rgn_code | rec_rgn_name | rec_agency_code | trans_amt | count |
|---|---|---|---|---|
| 530000 | 云南省本级 | 36299bf16778469f9c5eafdbf16cc588 | 63371 | 291 |
| 530000 | 云南省本级 | db33a748c53e4f70b8c71569127f71df | 2936 | 129 |
| 530000 | 云南省本级 |  | 2541 | 9 |
| 530100 | 昆明市本级 | 62aa363159804af19811045eeef897f0 | 2541 | 8 |
| 530000 | 云南省本级 | 808548570b444a3ca6d9c1b4ed5428b7 | 664.62 | 33 |
| 530000 | 云南省本级 | dd9c08b7a7b948f795ec3f26f05ccdd9 | 324 | 8 |
| 530000 | 云南省本级 | 5c3391a145e546c9b5f61a512b590516 | 100 | 1 |
| 000000 | 中央 | df155e380d804b90be68033d4333a80b | 30 | 2 |
| 530102 | 五华区 | 808548570b444a3ca6d9c1b4ed5428b7 |  | 1 |

**cube 生成 SQL**

```sql
-- table[0] 划拨金额：划入区划×划入单位（清分流向）
SELECT `fiscal_allocation`.`frecrgncode` `fiscal_allocation_view__rec_rgn_code`, `fiscal_allocation`.rec_rgn_name_canon `fiscal_allocation_view__rec_rgn_name`, `fiscal_allocation`.`frecagenidcode` `fiscal_allocation_view__rec_agency_code`, sum(`fiscal_allocation`.`ftransamt`) `fiscal_allocation_view__trans_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
GROUP BY 1, 2, 3
ORDER BY  4  DESC
LIMIT 100
```

### q27　财政专户收入和国库收入分别是多少？

- 判定：answer（21.3s）
- 摘要：可答（超出 08 文件「答不了」预期）：预算管理样式 bgt_style 可分档作答。

**清分收入按资金归口（bgt_style，全时段）**（3 行）
| bgt_style | im_amt | count |
|---|---|---|
| 1 | 16016039490.68 | 644 |
| 2 | 39377 | 78 |
| 4 | 600 | 6 |

**cube 生成 SQL**

```sql
-- table[0] 清分收入按资金归口（bgt_style，全时段）
SELECT `fiscal_allocation`.`fbgtstyle` `fiscal_allocation_view__bgt_style`, sum(`fiscal_allocation`.`fimamt`) `fiscal_allocation_view__im_amt`, count(*) `fiscal_allocation_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT t.*, c.chg_agency_name_canon FROM fne_funddivide_transfer t
      LEFT JOIN (SELECT fchgagencode,
                        arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                 FROM fne_funddivide_transfer GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
    ) x1
    LEFT JOIN (SELECT frecrgncode,
                      arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
               FROM fne_funddivide_transfer WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
  ) x2
  LEFT JOIN (SELECT fitemcode,
                    arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
             FROM fne_funddivide_transfer WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
) x3
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_funddivide_transfer WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x3.frecsubcode = rs.frecsubcode
)  AS `fiscal_allocation`
GROUP BY 1
ORDER BY  2  DESC
LIMIT 100
```

### q28　2022 年缴款金额排名前 10 的缴款人

- 判定：answer（26.2s）
- 摘要：空集：付款人名称 payer_name 已建模但库内为脱敏空值，返回 0 行。

**2022年缴款金额排名前10的缴款人（按 pay_date，金额=amt）**（1 行）
| payer_name | amt | count |
|---|---|---|
|  | 18208936572.27 | 385 |

**cube 生成 SQL**

```sql
-- table[0] 2022年缴款金额排名前10的缴款人（按 pay_date，金额=amt）
SELECT (NULL) `fiscal_collection_view__payer_name`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt`, count(*) `fiscal_collection_view__count` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (toDateOrNull(`fiscal_collection`.`fdate`) >= parseDateTimeBestEffort(?) AND toDateOrNull(`fiscal_collection`.`fdate`) <= parseDateTimeBestEffort(?))
GROUP BY 1
ORDER BY  2  DESC
LIMIT 102022-01-01T00:00:00.000Z2022-12-31T23:59:59.999Z
```

### q29　汇缴缴款的缴款明细记录有哪些？

- 判定：ask→追问→answer（51.4s）
- 摘要：追问后可答：bus_type=2（汇缴）明细可查。

**汇缴缴款明细（bus_type=2，前 100 行，按缴款日期倒序）**（20 行）
| pay_code | pay_date | chg_agency_code | chg_agency_name | sub_code | sub_name | count | amt |
|---|---|---|---|---|---|---|---|
| 53000026000000391098 | 2026-06-15T16:00:00.000 | 124045 | 001 / 测试云南测试环境 / 测试云南测试环境(试用版) / 测试云南测试环境(试用版)(试用版) | 1030110 | 民航发展基金收入 | 1 | 20000 |
| 53000026000000391100 | 2026-06-15T16:00:00.000 | 124045 | 001 / 测试云南测试环境 / 测试云南测试环境(试用版) / 测试云南测试环境(试用版)(试用版) | 103010201 | 中央农网还贷资金收入 / 中央农网还贷资金收入25 | 1 | 65017.59 |
| 53000026000000391080 | 2026-06-15T16:00:00.000 | 124045 | 001 / 测试云南测试环境 / 测试云南测试环境(试用版) / 测试云南测试环境(试用版)(试用版) | 103042758 | 高等学校住宿费 | 1 | 14820171 |
| 53000026904000000036 | 2026-06-05T16:00:00.000 | 998017 | 通用测试单位070301 | 1030110 | 民航发展基金收入 | 1 | 301.98 |
| 53000026904000000010 | 2026-06-05T16:00:00.000 | 998017 | 通用测试单位070301 | 1030110 | 民航发展基金收入 | 1 | 402.64 |
| 53010226821000000227 | 2026-04-02T16:00:00.000 | 125026 | 云南医保测试单位改名 / 开票点一 / 李思维 | 1030115 | 港口建设费收入 | 2 | 1981.32 |
| 53010026000000390247 | 2026-01-12T16:00:00.000 | 124992 | 云南信息技术中心 / 信息技术中心 | 103010201 | 中央农网还贷资金收入 / 中央农网还贷资金收入25 | 1 | 484 |
| 53010026000000390247 | 2026-01-12T16:00:00.000 | 124992 | 云南信息技术中心 / 信息技术中心 | 1030115 | 港口建设费收入 | 2 | 528 |
| 53010026000000390247 | 2026-01-12T16:00:00.000 | 124992 | 云南信息技术中心 / 信息技术中心 | 103042758 | 高等学校住宿费 | 1 | 324 |
| 53010026000000390247 | 2026-01-12T16:00:00.000 | 124992 | 云南信息技术中心 / 信息技术中心 | 1030110 | 民航发展基金收入 | 1 | 396 |
| 53000025907000000033 | 2025-10-14T16:00:00.000 | 998021 | 云南医疗测试单位10131 | 103010201 | 中央农网还贷资金收入 / 中央农网还贷资金收入25 | 1 | 632.36 |
| 53000025907000000033 | 2025-10-14T16:00:00.000 | 998021 | 云南医疗测试单位10131 | 1030121 | 旅游发展基金收入 | 1 | 3120 |
| 53010025000000389434 | 2025-10-14T16:00:00.000 | 124994 | 云南发展改革委员会 / 开票点001 / 开票点002 | 103010201 | 中央农网还贷资金收入 / 中央农网还贷资金收入25 | 1 | 100 |
| 53000025821000000570 | 2025-07-28T16:00:00.000 | 125026 | 云南医保测试单位改名 / 开票点一 / 李思维 | 1030110 | 民航发展基金收入 | 1 | 861 |
| 53000025849000000268 | 2025-06-17T16:00:00.000 | 999012 | 智能核销单位0408 | 1030115 | 港口建设费收入 | 1 | 123 |
| 53000025902000000065 | 2025-06-17T16:00:00.000 | 425107 | 云南测试单位95 | 1030115 | 港口建设费收入 | 1 | 123 |
| 53000025902000000030 | 2025-06-16T16:00:00.000 | 425107 | 云南测试单位95 | 1030121 | 旅游发展基金收入 | 1 | 369 |
| 53000025902000000049 | 2025-06-16T16:00:00.000 | 425107 | 云南测试单位95 | 1030121 | 旅游发展基金收入 | 1 | 123 |
| 53000025902000000057 | 2025-06-16T16:00:00.000 | 425107 | 云南测试单位95 | 1030121 | 旅游发展基金收入 | 1 | 246 |
| 53000025849000000209 | 2025-06-15T16:00:00.000 | 999012 | 智能核销单位0408 | 1030115 | 港口建设费收入 | 1 | 123 |

**汇缴缴款汇总（bus_type=2，全量单行聚合）**（1 行）
| count | paybook_count | amt |
|---|---|---|
| 209 | 120 | 2284794298.882 |

**cube 生成 SQL**

```sql
-- table[0] 汇缴缴款明细（bus_type=2，前 100 行，按缴款日期倒序）
SELECT `fiscal_collection`.`fpaycode` `fiscal_collection_view__pay_code`, toTimeZone(toDateTime64(toDateOrNull(`fiscal_collection`.`fdate`), 0), 'UTC') `fiscal_collection_view__pay_date`, `fiscal_collection`.`fchgagencode` `fiscal_collection_view__chg_agency_code`, `fiscal_collection`.chg_agency_name_canon `fiscal_collection_view__chg_agency_name`, `fiscal_collection`.`fsubcode` `fiscal_collection_view__sub_code`, `fiscal_collection`.sub_name_canon `fiscal_collection_view__sub_name`, count(*) `fiscal_collection_view__count`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fbustype` = ?)
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY  2  DESC
LIMIT 1002

-- table[1] 汇缴缴款汇总（bus_type=2，全量单行聚合）
SELECT count(*) `fiscal_collection_view__count`, COUNT(DISTINCT `fiscal_collection`.`fpaycode`) `fiscal_collection_view__paybook_count`, sum(`fiscal_collection`.`famt`) `fiscal_collection_view__amt` 
FROM  (SELECT * FROM (
  SELECT * FROM (
    SELECT * FROM (
      SELECT * FROM (
        SELECT t.*, c.chg_agency_name_canon FROM fne_paybook_full_high t
        LEFT JOIN (SELECT fchgagencode,
                          arrayStringConcat(arraySort(groupUniqArray(fchgagenname)), ' / ') AS chg_agency_name_canon
                   FROM fne_paybook_full_high GROUP BY fchgagencode) c ON t.fchgagencode = c.fchgagencode
      ) x1
      LEFT JOIN (SELECT frecrgncode,
                        arrayStringConcat(arraySort(groupUniqArray(frecrgnname)), ' / ') AS rec_rgn_name_canon
                 FROM fne_paybook_full_high WHERE frecrgncode != '' GROUP BY frecrgncode) r ON x1.frecrgncode = r.frecrgncode
    ) x2
    LEFT JOIN (SELECT fitemcode,
                      arrayStringConcat(arraySort(groupUniqArray(fitemname)), ' / ') AS item_name_canon
               FROM fne_paybook_full_high WHERE fitemcode != '' GROUP BY fitemcode) i ON x2.fitemcode = i.fitemcode
  ) x3
  LEFT JOIN (SELECT fsubcode,
                    arrayStringConcat(arraySort(groupUniqArray(fsubname)), ' / ') AS sub_name_canon
             FROM fne_paybook_full_high WHERE fsubcode != '' GROUP BY fsubcode) s ON x3.fsubcode = s.fsubcode
) x4
LEFT JOIN (SELECT frecsubcode,
                  arrayStringConcat(arraySort(groupUniqArray(frecsubname)), ' / ') AS rec_sub_name_canon
           FROM fne_paybook_full_high WHERE frecsubcode != '' GROUP BY frecsubcode) rs ON x4.frecsubcode = rs.frecsubcode
)  AS `fiscal_collection`
WHERE (`fiscal_collection`.`fbustype` = ?)
LIMIT 1002
```

### q30　各笔缴款的到账日期和退付金额是多少？

- 判定：nomatch（22.7s）
- 摘要：nomatch：退付相关成员（refund 等）在模型面全空，无法作答。

