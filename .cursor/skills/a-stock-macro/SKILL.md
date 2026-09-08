---
name: a-stock-macro
description: >-
  获取A股新闻资讯、宏观数据、指数成分/权重/估值、交易日历与ETF期权（T型报价/希腊字母/IV）：东财/财联社新闻、社融、PMI、中证国证指数、深交所日历。在用户查新闻、宏观、指数或期权时使用。
origin: custom
version: 3.8.0
---

> 📦 拆分自 [a-stock-data](https://github.com/simonlin1212/a-stock-data) V3.8.0 — 接口语义未改，仅按场景重组。
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)


# A股新闻·宏观·指数·期权（a-stock-macro）

> **前置依赖：** 使用任一东财 / 通达信端点前，先读取并执行 [`a-stock-core`](../a-stock-core/SKILL.md) 的共用 helper（`norm_ticker` / `em_get` / `tdx_client` / 防封规则）。


## When to Activate

分四块，互不混用：

1. **新闻**：个股新闻、财联社电报、全球资讯
2. **ETF 期权**：合约清单、T型报价、希腊字母与 IV
3. **宏观**：人民银行社融、国家统计局 PMI
4. **指数与交易日历**：中证/国证成分与权重、中证估值、深交所整月日历；北交所行情备胎见 capital/core fallback

关键词：新闻、财联社、社融、PMI、指数成分、指数权重、交易日历、ETF期权、隐含波动率

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_ticker(code)` | 任意写法→纯6位（`SH600519`/`600519.SH` 皆可；解析失败抛错不返空） | 本地 |
| 5.1 | `eastmoney_stock_news(code)` | 个股新闻 | 东财 |
| 5.2 | `cls_telegraph()` | 财联社电报（7×24，本地签名零key） | 财联社 |
| 5.3 | `eastmoney_global_news()` | 全球资讯（7×24） | 东财 |
| 9.1 | `sina_option_codes` / `sina_option_tquote` / `sina_option_greeks` | ETF期权合约清单 / T型报价 / 希腊字母+IV | 新浪 |
| 11.1 | `pboc_social_financing(year)` | 社会融资规模增量（月度12列） | 人民银行 |
| 11.2 | `nbs_pmi()` | 制造业/非制造业/综合 PMI + 大中小型企业 | 国家统计局 |
| 12.1 | `index_constituents(index_code, provider)` | 最近公布的沪深北指数成分；csi/cni 显式选源 | 中证/国证 |
| 12.2 | `index_weights(index_code, provider)` | 最近公布的指数权重（百分数），保留真实日期 | 中证/国证 |
| 12.3 | `index_valuation(index_code)` | 两种口径 PE、股息率；不含 PB | 中证 |
| 12.4 | `trading_calendar(year, month)` | 官方整月交易日历 | 深交所 |


完整可运行代码见 [reference-endpoints.md](reference-endpoints.md)。

