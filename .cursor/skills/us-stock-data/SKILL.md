---
name: us-stock-data
description: >-
  美股全栈数据工具包路由索引。按场景分发到 us-stock-core / quote / research /
  pulse / capital / fundamentals / macro。当用户笼统要求「用美股数据取数」或
  不确定该用哪一层时加载本索引；具体取数请再打开对应场景 skill。
origin: custom
version: 1.0.0
---

# 美股数据路由（us-stock-data）

与 [`a-stock-data`](../a-stock-data/SKILL.md) 对称的美股侧索引。**不要**在本文件内重复贴长代码；打开对应子 skill。

## 何时用本索引

- 用户说「美股取数 / Yahoo / SEC / FRED」但未指定场景  
- 投研 skill 需要决定先加载哪一层  
- 对照 A 股某层找美股等价层  

## 场景分发

| 场景 | 加载 skill | 典型问题 |
|------|------------|----------|
| 共用底座 / ticker / 限流 | [`us-stock-core`](../us-stock-core/SKILL.md) | 归一化、User-Agent、环境变量 |
| 行情 / K 线 / 估值快照 | [`us-stock-quote`](../us-stock-quote/SKILL.md) | 现价、市值、前向 PE、历史价 |
| 财报 / SEC / 估值历史 | [`us-stock-fundamentals`](../us-stock-fundamentals/SKILL.md) | 三表、10-K/10-Q、PE 分位 |
| 一致预期 / 目标价 | [`us-stock-research`](../us-stock-research/SKILL.md) | 分析师目标价、财报日 |
| 新闻 / 宏观 | [`us-stock-macro`](../us-stock-macro/SKILL.md) | 个股新闻、FRED |
| 机构 / 内部人 / 分红 | [`us-stock-capital`](../us-stock-capital/SKILL.md) | 13F 摘要、Form 4 |
| 情绪 / 相对强弱 / IV | [`us-stock-pulse`](../us-stock-pulse/SKILL.md) | vs SPY、期权 IV |

## 与 A 股对照

| A 股层 | 美股层 | 主要源差异 |
|--------|--------|------------|
| a-stock-core | us-stock-core | Yahoo/SEC vs 通达信/东财 |
| a-stock-quote | us-stock-quote | yfinance |
| a-stock-fundamentals | us-stock-fundamentals | SEC EDGAR + Yahoo 财务 |
| a-stock-research | us-stock-research | 无东财 PDF；Yahoo/Finnhub 预期 |
| a-stock-macro | us-stock-macro | FRED vs 东财宏观 |
| a-stock-capital | us-stock-capital | 13F/Form4 vs 两融/北向 |
| a-stock-pulse | us-stock-pulse | 无涨停池；相对强弱/IV |

## 投研默认取数顺序

1. `us-stock-core` → `quote`（现价与估值快照）  
2. `fundamentals`（三表 + SEC 列表）  
3. `research`（目标价 / EPS 预期）  
4. `macro`（新闻催化）  
5. 需要时再补 `capital` / `pulse`（旁证、降权）  

## 环境变量

见 `us-stock-core`：`FINNHUB_API_KEY`、`FRED_API_KEY`、`POLYGON_API_KEY`（均可选）。
