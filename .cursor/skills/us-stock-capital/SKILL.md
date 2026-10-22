---
name: us-stock-capital
description: >-
  获取美股资金与持股数据：机构持仓比例摘要、内部人交易(Form4入口)、分红与回购线索。
  在用户查美股13F、内部人买卖、回购或分红时使用。不作投研主结论。
origin: custom
version: 1.0.0
---

# 美股资金与持股（us-stock-capital）

> **前置依赖：** [`us-stock-core`](../us-stock-core/SKILL.md)。

## When to Activate

- 机构持仓比例、大股东摘要
- Form 4 内部人买卖入口
- 股息率、回购相关公开字段
- 关键词：13F、insider、buyback、dividend

## 纪律

- **降权**：资金流/热度不作价值或成长结论主证据（同 a-stock-capital）  
- 13F 有季度延迟；Form 4 更及时但噪声大  
- 完整 13F 持仓解析较重；本 skill 先给摘要 + SEC 入口  

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 5.1 | `yahoo_holders_summary(ticker)` | 机构/内部人持股比例 | yfinance |
| 5.2 | `yahoo_insider_transactions(ticker)` | 内部人交易表 | yfinance |
| 5.3 | `sec_form4_filings(ticker)` | 近期 Form 4 列表 | SEC |

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
