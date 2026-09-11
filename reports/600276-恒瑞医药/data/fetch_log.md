# 取数日志｜600276 恒瑞医药

- 财务时点：2026-06-30（最新完整报告期：2026 年中报）；最新年报 2025-12-31
- 行情快照：2026-09-11 腾讯 `tencent_quote`
- 估值序列末日：2026-09-11（baostock，交易日）
- 催化检索时点：2026-09-11（东财新闻 + Web「下跌原因/创新药」+ 巨潮公告）
- 脚本：`fetch_research.py`（TARGET=600276；PEERS=复星/科伦/长春高新/凯莱英）

## 成功

| 数据 | 接口 | 文件 |
|------|------|------|
| 现价/PE/PB/市值 | 腾讯 | `quotes.json` |
| 三表（标的+同业） | 新浪 | `sina_financials.json` |
| 衍生 KPI | 脚本派生 | `derived_kpis.json` `sina_latest_keys.json` |
| 估值历史 PE/PB/PS | baostock 2018–2026 | `valuation_history.csv` `valuation_percentiles.json` |
| 约 400 日价格路径 | baostock | `price_path_400d.json` |
| 同业估值截面 | baostock | `peer_valuation.json` |
| 一致预期 EPS | 同花顺 | `ths_eps.json` |
| 研报 56 篇 | 东财 reportapi | `reports.json` |
| 个股新闻 50 | 东财 search | `news.json` |
| 公告 30 | 巨潮 | `announcements.json` |
| Web 催化摘要 | WebSearch | `web_catalyst_notes.md` |
| 运行日志 | 本脚本 | `fetch_log.json` |

## 失败

1. **东财 `stock_info`（push2.eastmoney.com）**：ProxyError / RemoteDisconnected — 未写出 `stock_info.json`（行业/股本等需改用腾讯行情或年报）。
2. **通达信 `tdx_client()` / mootdx**：候选服务器均无法取数 — 未写出 `tdx_snapshot.json`；日 K / F10 缺失，价格序列已用 baostock 替代。

## Web 补充（催化，非接口）

详见 `web_catalyst_notes.md`：H1'26 业绩失速（营收/扣非承压、肿瘤创新药仅个位数增长、仿制药出清、BD 波动、汇兑损失、FDA 生产端 CRL 叙事）；估值从“药茅溢价”向成长验证切换；2024/2025 创新药收入与 2026–28 管线兑现预期。
