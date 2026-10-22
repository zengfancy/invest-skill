---
name: us-stock-research
description: >-
  获取美股卖方预期与研究线索：分析师目标价/评级摘要、盈利预期、财报指引窗口、
  SEC重要申报入口。在用户查美股一致预期、目标价、earnings guide或电话会时使用。
origin: custom
version: 1.0.0
---

# 美股研报与一致预期（us-stock-research）

> **前置依赖：** [`us-stock-core`](../us-stock-core/SKILL.md)。

## When to Activate

- 分析师目标价、评级（buy/hold/sell 摘要）
- 前瞻 EPS / 收入预期
- 下一财报日、指引相关公开信息
- 关键词：美股一致预期、target price、earnings estimate、评级

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 3.1 | `yahoo_analyst_summary(ticker)` | 目标价、推荐、EPS 预期 | yfinance |
| 3.2 | `yahoo_earnings_dates(ticker)` | 财报日程与 surprise | yfinance |
| 3.3 | `finnhub_recommendation(ticker)` | 评级变迁（需 Key，可选） | Finnhub |

## 纪律

- 卖方目标价 **不是** 本仓库投研结论；只作预期差对照  
- 免费源的「一致预期」粒度粗于同花顺；缺口标明  
- 电话会全文常需付费；可用 8-K / 新闻摘要代替并注明  

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
