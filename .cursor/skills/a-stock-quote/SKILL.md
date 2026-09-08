---
name: a-stock-quote
description: >-
  拉取A股实时行情与K线：通达信K线/五档/逐笔、腾讯PE/PB/市值/换手、百度带均线日K、新浪复权因子。在用户要查股价、盘口、K线、复权、涨跌停价、指数或ETF报价时使用。
origin: custom
version: 3.8.0
---

> 📦 拆分自 [a-stock-data](https://github.com/simonlin1212/a-stock-data) V3.8.0 — 接口语义未改，仅按场景重组。
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)


# A股行情层（a-stock-quote）

> **前置依赖：** 使用任一东财 / 通达信端点前，先读取并执行 [`a-stock-core`](../a-stock-core/SKILL.md) 的共用 helper（`norm_ticker` / `em_get` / `tdx_client` / 防封规则）。


## When to Activate

- 拉实时行情（价格 / 五档盘口 / K线 / 涨跌停价）
- 查腾讯 PE/PB/市值/换手率快照、指数/ETF 报价
- 需要复权因子或把不复权 K 线做前/后复权
- 关键词：K线、盘口、逐笔、实时价、复权、qfq、hfq、涨跌停、指数行情、ETF行情

## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_ticker(code)` | 任意写法→纯6位（`SH600519`/`600519.SH` 皆可；解析失败抛错不返空） | 本地 |
| 1.1 | `tdx_client()` → `.bars()` / `.quotes()` / `.transaction()` | K线(多周期,不复权) / 五档盘口 / 逐笔成交 | 通达信 |
| 1.2 | `tencent_quote(codes)` | 实时价/PE/PB/市值/换手/涨跌停/指数/ETF（带 `is_stale` 僵尸报价标志） | 腾讯 |
| 1.3 | `baidu_kline_with_ma(code)` | 日K线带 MA5/10/20 | 百度 |
| 1.4 | `sina_adjust_factor(code, kind)` / `apply_adjust(bars, factors)` | 复权因子 qfq/hfq + 套用到不复权K线 | 新浪 |


## 选用原则

- K线/五档/逐笔：优先通达信 `tdx_client()`（不封 IP）
- 估值快照/市值/换手：腾讯 `tencent_quote`
- 带 MA 的日K：百度 `baidu_kline_with_ma`
- 跨除权比较前：新浪 `sina_adjust_factor` + `apply_adjust`

完整可运行代码见 [reference-endpoints.md](reference-endpoints.md)。

