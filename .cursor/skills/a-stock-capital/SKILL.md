---
name: a-stock-capital
description: >-
  获取A股资金面与筹码数据：融资融券、大宗交易、股东户数、分红送转、个股资金流、筹码分布，以及沪深官方两融备胎。在用户查两融、大宗、筹码或资金流向时使用。
origin: custom
version: 3.8.0
---

> 📦 拆分自 [a-stock-data](https://github.com/simonlin1212/a-stock-data) V3.8.0 — 接口语义未改，仅按场景重组。
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)


# A股资金面与筹码（a-stock-capital）

> **前置依赖：** 使用任一东财 / 通达信端点前，先读取并执行 [`a-stock-core`](../a-stock-core/SKILL.md) 的共用 helper（`norm_ticker` / `em_get` / `tdx_client` / 防封规则）。


## When to Activate

- 融资融券、大宗交易、股东户数、分红送转
- 个股资金流（120日）、筹码分布（获利比例/成本区间）
- 关键词：两融、融资余额、大宗、股东户数、分红、派息、资金流、筹码、CYQ

## 依赖说明

- `chip_distribution` 需要 OHLC + 换手率序列：行情用 [`a-stock-quote`](../a-stock-quote/SKILL.md)，
  历史换手可用 [`a-stock-fundamentals`](../a-stock-fundamentals/SKILL.md) 的 `baostock_valuation_history`。
- 沪深官方两融 / 北交所行情备胎收录于本 skill 的 reference；执行前须先跑
  [`a-stock-macro`](../a-stock-macro/reference-endpoints.md) 中 Layer 12 的自包含 helper 代码块。

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_ticker(code)` | 任意写法→纯6位（`SH600519`/`600519.SH` 皆可；解析失败抛错不返空） | 本地 |
| 4.1 | `margin_trading(code)` | 融资融券明细 | 东财 |
| 4.2 | `block_trade(code)` | 大宗交易+营业部 | 东财 |
| 4.3 | `holder_num_change(code)` | 股东户数变化 | 东财 |
| 4.4 | `dividend_history(code)` | 分红送转历史 | 东财 |
| 4.5 | `stock_fund_flow_120d(code)` | 个股资金流（120日，日级） | 东财 |
| 4.6 | `chip_distribution(df)` | 筹码分布（获利比例/平均成本/90-70成本区间/筹码峰） | 本地计算 |
| 官方备胎扩展 | `margin_trading_backup(date, exchange, code=None)` | 单所两融明细（先执行 §12 helper） | 上交所/深交所 |
| 官方备胎扩展 | `bse_quote_backup(date, code=None)` | 北交所全板/单票当前快照（先执行 §12 helper） | 北交所 |


完整可运行代码见 [reference-endpoints.md](reference-endpoints.md)。

