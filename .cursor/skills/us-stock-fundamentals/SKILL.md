---
name: us-stock-fundamentals
description: >-
  获取美股基本面与估值：损益/资产负债/现金流、业务分部、分析师预期摘要、估值倍数与
  GAAP/Non-GAAP纪律、SEC 10-K/10-Q入口。在用户查美股财报、FCF、分部或估值历史时使用。
origin: custom
version: 1.0.0
---

# 美股基本面与估值（us-stock-fundamentals）

> **前置依赖：** [`us-stock-core`](../us-stock-core/SKILL.md)。

## When to Activate

- 三表、毛利率、经营利润、FCF、净现金
- 业务分部 / geographic segments
- trailing / forward PE、EV/EBITDA、PS
- 10-K / 10-Q 链接与关键摘录入口
- 关键词：美股财报、Non-GAAP、分部、FCF、10-K

## 硬纪律

1. **GAAP 与 Non-GAAP 分列**；投研结论写明用哪套  
2. 稀释后股本（diluted shares）做 EPS  
3. 分部以 10-K Note / yfinance `incomestmt` 附注为准，禁止自创板块名  
4. 取不到写「未取得」，禁止臆造  

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 2.1 | `yahoo_financials(ticker)` | 年/季 三表 | yfinance |
| 2.2 | `yahoo_key_metrics(ticker)` | PE/PS/EV、利润率、FCF 线索 | yfinance info |
| 2.3 | `yahoo_earnings_trend(ticker)` | 分析师预期摘要 | yfinance |
| 2.4 | `sec_company_tickers()` / `sec_recent_filings(cik)` | CIK 与近期申报 | SEC |
| 估值 | `forward_pe` / `calc_peg` | 前向 PE / PEG | 本地 |

完整代码见 [reference-endpoints.md](reference-endpoints.md)。
