---
name: us-stock-quote
description: >-
  拉取美股实时/收盘行情与K线：yfinance现价、市值、PE/PB、历史日K、指数(SPX/QQQ/VIX)。
  在用户要查美股股价、市值、K线、指数或ETF报价时使用。
origin: custom
version: 1.0.0
---

# 美股行情层（us-stock-quote）

> **前置依赖：** 先读取并执行 [`us-stock-core`](../us-stock-core/SKILL.md) 的共用 helper。

## When to Activate

- 美股现价、涨跌幅、市值、PE/PB 快照
- 日/周 K 线、复权收盘价
- 指数 / ETF：`^GSPC`、`^IXIC`、`^VIX`、`SPY`、`QQQ`
- 关键词：美股行情、AAPL 股价、纳指、标普、VIX

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_us_ticker` | ticker 归一 | 本地 |
| 1.1 | `yahoo_quote(tickers)` | 现价/市值/PE/PB/52w | yfinance |
| 1.2 | `yahoo_history(ticker, period, interval)` | OHLCV K线 | yfinance |
| 1.3 | `yahoo_index_snapshot()` | 标普/纳指/VIX 快照 | yfinance |

## 选用原则

- 个股与 ETF 一律 `norm_us_ticker` 后再查  
- 指数 Yahoo 符号带 `^`（`^GSPC`），不要当成普通股票归一掉  
- 盘中价可能延迟 15 分钟（免费源）；报告注明时点  

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
