---
name: us-stock-pulse
description: >-
  美股盘面与情绪辅助：板块相对强弱摘要、期权隐含波动粗览、短线热度线索。
  在用户看美股情绪、IV、板块对比时使用。不作价值/成长主结论。
origin: custom
version: 1.0.0
---

# 美股盘面与情绪（us-stock-pulse）

> **前置依赖：** [`us-stock-core`](../us-stock-core/SKILL.md)。

## When to Activate

- 个股相对 SPY/QQQ 的短期强弱
- 期权 IV / 成交量粗览（若有数据）
- 短线情绪辅助（涨跌归因旁证）
- 关键词：美股情绪、隐含波动、相对强弱

## 纪律

- **降权**：情绪/热度不作投研主证据  
- 美股无「涨停板」叙事；勿硬套 A 股打板框架  
- 免费源 IV 不稳定时标明缺口  

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 6.1 | `relative_strength(ticker, bench, days)` | 相对基准收益 | yfinance |
| 6.2 | `yahoo_options_iv_snapshot(ticker)` | 近月期权粗览 | yfinance |

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
