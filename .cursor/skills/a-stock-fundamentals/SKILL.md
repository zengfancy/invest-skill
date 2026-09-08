---
name: a-stock-fundamentals
description: >-
  获取A股基本面与历史估值：通达信财务/F10、东财资料、新浪三表、baostock估值历史与退市日、申万行业变迁，以及前向PE/PEG等估值公式。在用户查财报、估值历史或公司基本面时使用。
origin: custom
version: 3.8.0
---

> 📦 拆分自 [a-stock-data](https://github.com/simonlin1212/a-stock-data) V3.8.0 — 接口语义未改，仅按场景重组。
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)


# A股基本面与估值（a-stock-fundamentals）

> **前置依赖：** 使用任一东财 / 通达信端点前，先读取并执行 [`a-stock-core`](../a-stock-core/SKILL.md) 的共用 helper（`norm_ticker` / `em_get` / `tdx_client` / 防封规则）。


## When to Activate

- 通达信财务快照 / F10、东财股票资料
- 新浪财报三表、baostock 估值历史（PE/PB/PS + 换手/停牌/ST）
- 上市/退市日、申万行业变迁史
- 本地估值公式：前向PE / PEG / PE消化 / full_valuation
- 关键词：财报、三表、F10、估值历史、退市、申万、PEG、前向PE

## 重要限制

- **baostock 不支持北交所**（登录前应拦截并抛错）
- 申万历史分类仅有行业代码、无中文名

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_ticker(code)` | 任意写法→纯6位（`SH600519`/`600519.SH` 皆可；解析失败抛错不返空） | 本地 |
| 6.1 | `client.finance(symbol)` | 季报快照 37 字段 | 通达信 |
| 6.2 | `client.F10(symbol, name)` | 公司资料 9 大类文本 | 通达信 |
| 6.3 | `eastmoney_stock_info(code)` | 行业/股本/市值/上市日期 | 东财 |
| 6.4 | `sina_financial_report(code, type)` | 财报三表 | 新浪 |
| 6.5 | `baostock_valuation_history(code, s, e)` | 估值历史 PE/PB/PS/PCF + 换手率 + 停牌 + ST（**不支持北交所**） | baostock |
| 6.6 | `baostock_stock_basic(code)` | 上市日 / **退市日** / 状态 | baostock |
| 6.7 | `sw_industry_history()` / `sw_industry_as_of(df, code, d)` | 申万行业**变迁史**（消除前视偏差，仅代码无中文名） | 申万 |
| 估值公式 | `forward_pe` / `pe_digestion` / `calc_peg` / `full_valuation(code)` | 前向PE / PE消化时间 / PEG / 单票估值全景 | 本地计算 |


完整可运行代码见 [reference-endpoints.md](reference-endpoints.md)。

