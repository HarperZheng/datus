# Debug 记录

## 2026-10-16 `/tables` 报 UNKNOWN_TABLE(ClickHouse 23.3)

- **原因**:datus-clickhouse 查元数据用小写 `information_schema`,23.3 只认大写
- **修复 1**:`D:\develop\datus\Datus-agent\.venv\lib\python3.12\site-packages\datus_clickhouse\connector.py:158` 小写改大写 `INFORMATION_SCHEMA`
```
  # 改前
  f"FROM information_schema.{metadata_config.info_table} "
  # 改后
  f"FROM INFORMATION_SCHEMA.{metadata_config.info_table} "
```
- **修复 2**:CH 标识符大小写敏感,WHERE 里 `TABLE_SCHEMA` 对不上视图的小写列 → `connector.py:145/147/157` 同步改小写 `table_schema` / `table_name`
- **修复 3**:23.3 的 `table_type` 是数字编码(1=表 2=视图…)不是字符串,`IN ('BASE TABLE')` 报类型不匹配 → `connector.py` `_get_metadata` 里类型名映射为数字编码再拼 `IN`
- **注意**:`uv sync` 后补丁失效,需重打;回滚用 `uv sync --reinstall-package datus-clickhouse`

## 2026-10-19 query_metrics 报 Code 115 UNKNOWN_SETTING(ClickHouse 23.3)

- **现象**:datus 执行 query_metrics 时,ClickHouse 23.3 拒绝查询,报 `Code 115: Unknown setting session_timezone (UNKNOWN_SETTING)`
- **原因**:dosi-engine 0.1.13(Rust 原生扩展)在执行 SQL 前硬编码追加 `SETTINGS session_timezone = 'UTC'`;该设置 ClickHouse 23.5 才引入,23.3 按设置名直接拒绝,与值无关(改时区无效)
- **定位**:二进制分析 `_native.abi3.so` 确认:值是写死的常量,dosi-engine 不读系统时区;dry_run 只编译不执行,所以测不出这个问题
- **修复**(2026-10-19 已实现):datus 在 `dosi/engine.py::_runtime_connections` 挂 ClickHouse 兼容切面,非本机 CH 连接时 dosi 的 HTTP 流量改走进程内反代(`ch_compat.py`,127.0.0.1 临时端口 daemon 线程)
- **逻辑**:反代转发时剥掉 URL 里的 `session_timezone` 参数、把 body 里的 `dateTrunc('month',col)` 改写成 `toStartOfMonth(col)` 等 23.3 兼容函数;`DATUS_CH_COMPAT=off` 禁用;改在 datus 仓库内,uv sync 不冲掉
- **现状**:单测 93 通过;真机 CH(172.18.166.126)三基准值验证待做
