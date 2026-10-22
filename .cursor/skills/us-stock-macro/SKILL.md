---
name: us-stock-macro
description: >-
  获取美股相关新闻与宏观数据：Yahoo个股新闻、可选Finnhub新闻、FRED利率/CPI等。
  在用户查美股新闻催化、美联储利率、通胀或宏观背景时使用。
origin: custom
version: 1.0.0
---

# 美股新闻与宏观（us-stock-macro）

> **前置依赖：** [`us-stock-core`](../us-stock-core/SKILL.md)。

## When to Activate

- 个股近期新闻 / 催化检索（涨跌归因前必做）
- 联邦基金利率、CPI、失业率等宏观序列
- 关键词：美股新闻、美联储、CPI、非农、FRED

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 4.1 | `yahoo_news(ticker, limit)` | 个股新闻标题与链接 | yfinance |
| 4.2 | `finnhub_company_news(ticker, frm, to)` | 公司新闻（需 Key） | Finnhub |
| 4.3 | `fred_series(series_id)` | 宏观时间序列 | FRED |

## 催化保鲜（投研 Step 涨跌前）

1. 拉近 7–14 天个股新闻  
2. Web 检索 `{公司名} stock drop reason` / `{ticker} earnings`  
3. 媒体共识与 10-Q/8-K 事实分开写  

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
