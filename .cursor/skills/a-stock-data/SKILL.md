---
name: a-stock-data
description: >-
  A股全栈数据工具包路由索引（V3.8.0 拆分版）。按场景分发到 a-stock-core / quote /
  research / pulse / capital / fundamentals / macro。当用户笼统要求「用 a-stock-data
  取数」或不确定该用哪一层时加载本索引；具体取数请再打开对应场景 skill。
origin: custom
version: 3.8.0
---

> 📦 项目主页：https://github.com/simonlin1212/a-stock-data — 更新、反馈、支持作者
>
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)
>
> 本目录为 **V3.8.0 拆分后的薄路由**。可运行代码已迁至各场景 skill 的 `reference-endpoints.md`，接口语义与上游一致。

# A股全栈数据工具包（路由索引）

## 怎么用

1. 先读并执行 [`a-stock-core`](../a-stock-core/SKILL.md)（`norm_ticker` / `em_get` / `tdx_client` / 防封）。
2. 按需求打开下表对应场景 skill；需要代码时再读其 `reference-endpoints.md`。
3. 东财主源被封时，查 core 的 [reference-fallback.md](../a-stock-core/reference-fallback.md)。

## 场景对照

| Skill | 覆盖原层 | 典型用途 |
|-------|----------|----------|
| [a-stock-core](../a-stock-core/SKILL.md) | 共用 helper | ticker / 通达信 / 东财限流 / 防封 |
| [a-stock-quote](../a-stock-quote/SKILL.md) | L1 | K线、盘口、实时价、复权 |
| [a-stock-research](../a-stock-research/SKILL.md) | L2+L7 | 研报、一致预期、iwencai、公告 |
| [a-stock-pulse](../a-stock-pulse/SKILL.md) | L3+L8+L10 | 热点、龙虎榜、涨停、热榜、互动易 |
| [a-stock-capital](../a-stock-capital/SKILL.md) | L4 | 两融、大宗、股东、分红、资金流、筹码 |
| [a-stock-fundamentals](../a-stock-fundamentals/SKILL.md) | L6 | 财报、F10、估值历史、申万 |
| [a-stock-macro](../a-stock-macro/SKILL.md) | L5+L9+L11+L12 | 新闻、期权、社融/PMI、指数与日历 |

完整函数级路由：[reference-routing.md](../a-stock-core/reference-routing.md)

## 依赖安装

```bash
pip install mootdx requests pandas stockstats numpy baostock xlrd openpyxl
```

iwencai 语义搜索另需 API Key，见 [a-stock-research](../a-stock-research/SKILL.md)。

## 溯源

- 上游版本：V3.8.0
- 整合记录：[docs/source-integration-v3.8.0.md](../a-stock-core/docs/source-integration-v3.8.0.md)
- License：[../a-stock-core/LICENSE](../a-stock-core/LICENSE)
