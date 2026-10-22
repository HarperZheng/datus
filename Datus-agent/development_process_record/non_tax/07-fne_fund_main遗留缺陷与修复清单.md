
# 遗留缺陷与修复清单（除零保护与脏数据基准化之外）

> 2026-10-20 P0/P1 验收收尾时登记的剩余待修复项。范围：**不含**两项已明确暂缓的问题——① 清分率 compose 除零保护（空集 Code 153，任务 #3，用户暂缓）；② 测试环境脏数据导致 §七.5 冒烟题需重新基准化（2025-08 无清分数据，任务 #4）。本清单按严重度分 A/B/C/D 四档。

## A 级：链路缺陷（已复现的报错）

### 1. execute_sql 直查路径暴露 Code 115（任务 #5）

- **证据**：冒烟 run payload 68/71，agent 走 `execute_sql` 直连 ClickHouse 两次命中 `Code 115 Unknown setting`（session_timezone）——`ch233_compat` 代理只包裹 dosi 引擎路径，`db_tools.execute_sql` 直连不经过它。agent 当时靠子查询绕过，但每次直查都在赌。
- **修法**：execute_sql 的 ClickHouse 连接同样过 `reroute_entry`，让代理覆盖所有 CH 出口。

### 2. paybook clear_date 表达式不防脏值（任务 #6）

- **证据**：`paybook_full_high.fcleardate` 存在 length<10 的脏串（冒烟实测），`toDate(fcleardate)` 直查抛 **Code 38 Cannot parse date**。当前 16 个指标都走 `fill_date`（干净）所以没炸，但 `clear_date` 是已声明维度字段、可经 R1 边做维度——任何人按"清分日期"分组/过滤就会失败。
- **修法**：表达式改 `toDateOrNull(fcleardate)`（防御式落 NULL），走 semantic_modeling。
- **对照组实测**：funddivide 侧 `cleardate` 干净（引擎 cleardate 轴查询通过，2022 全年 68,453），`fill_date` 干净。

## B 级：口径缺陷（不报错，但数字错）

### 3. 汇总批次数 expression 含空串假批次（任务 #7）

- **证据**：`COUNT(DISTINCT fcollectid)` 实测 = 429，排除空串后 428——CH 的 uniqExact 把 `''` 计成 1 个批次。instructions 已写死口径但是软约束，agent 不执行时照样返回 429。
- **修法**：expression 改 `uniqExactIf(funddivide_transfer.fcollectid, fcollectid != '')`，走 semantic_modeling；改前需在 03 清单补批次数基准数字（§七.4 目前没有这项）。

### 4. 缴库去重的确定性靠巧合（验证过，暂不炸）

- **证据**：编译出的去重是 `row_number() OVER (PARTITION BY fid)` 无 ORDER BY——行选择是任意的。实测当前 429 个重复 fid 的 ftotalamt 全部一致（0 个变体），所以 SUM 稳定 = 29,535,106.14。但未来若同 fid 出现不同金额，去重会**静默变成随机取一行**。
- **修法（低优先）**：dedup dataset 源 SELECT 补确定性排序（如 `ORDER BY ftotalamt DESC` 或按业务规则选行）。

## C 级：检索/路由质量（不影响正确性）

### 5. 指标检索排序偏置

冒烟里 `search_metrics("清分金额")` 首位返回的是 `清分金额_环比` 而非基础指标——窗口派生指标在 RAG 里压过了同名基础指标。

### 6. agent 绕过 query_metrics 手写 SQL

语义命中后，最终查询没走指标编译而是裸 SQL。§七.5 的意图是验证指标路由；这次 partly 因为验收题数据缺失而复杂化，但值得在 chat 提示词里强化"命中指标必须走 query_metrics"。

## D 级：运营/文档

### 7. 验收跑批超时

340s 不够（GLM-5.3-Flash 经 relay，~50 次工具调用）——跑批放宽到 600s+ 或分步执行。

### 8. 划拨侧无对账基准

划拨完成 24,815 / 未划拨 47,692.62 只有自洽性检验（二者相加=全量），03 清单没有这两项的独立基准数字——补上才算真对账。

### 9. paybook ai_context 缺空键注记

722/1272 行空 `fcollectid`（未入批次），字段描述里有但 dataset 级口径没写——未来若有人声明 `paybook.fcollectid` 连边（`''=''` 配对 722×178），会复现假关联。补一句进 dataset ai_context。

## 优先级建议

A1（#5）> A2（#6）> B3（#7），这三个都是"下一次使用就会撞上"的；B4/C/D 可以攒着随下次建模一起处理。A2 和 B3 都要走 semantic_modeling 改 expression，可以合成一次建模会话做掉。
