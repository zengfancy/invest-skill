---
name: a-stock-research
description: >-
  获取A股研报与公司公告：东财研报列表/PDF、行业研报、同花顺一致预期EPS、iwencai语义搜索、巨潮公告。在用户要搜研报、一致预期、下载研报PDF或查公告时使用。
origin: custom
version: 3.8.0
---

> 📦 拆分自 [a-stock-data](https://github.com/simonlin1212/a-stock-data) V3.8.0 — 接口语义未改，仅按场景重组。
> 作者：Simon 林 · X [@linsizhen](https://x.com/linsizhen)


# A股研报与公告（a-stock-research）

> **前置依赖：** 使用任一东财 / 通达信端点前，先读取并执行 [`a-stock-core`](../a-stock-core/SKILL.md) 的共用 helper（`norm_ticker` / `em_get` / `tdx_client` / 防封规则）。


## When to Activate

- 搜个股/行业研报、下载研报 PDF
- 查同花顺一致预期 EPS
- iwencai 自然语言搜研报/选股（需 Key）
- 查巨潮公告全文 / 通达信最新提示
- 关键词：研报、评级、一致预期、EPS、iwencai、公告、巨潮、PDF

## iwencai API Key（仅语义搜索需要）

### iwencai API Key（仅语义搜索需要）

```bash
# 环境变量方式
export IWENCAI_API_KEY="your_key_here"
export IWENCAI_BASE_URL="https://openapi.iwencai.com"

# 申请地址: https://www.iwencai.com/skillhub
# 注册后安装 SkillHub CLI，再安装 report-search 技能即可获得 Key
```

其他数据源（mootdx / 腾讯 / 东财 / 同花顺 / 百度股市通 / 新浪 / 巨潮 / baostock / 申万 / 人民银行 / 国家统计局）全部免费，无需 key。



## 端点路由

| § | 函数 | 拿什么 | 源 |
|---|------|--------|----|
| 前置 | `norm_ticker(code)` | 任意写法→纯6位（`SH600519`/`600519.SH` 皆可；解析失败抛错不返空） | 本地 |
| 2.1 | `eastmoney_reports(code)` / `download_pdf(rec)` | 个股研报+评级+三年EPS / 研报PDF | 东财 |
| 2.1 | `eastmoney_industry_reports(industry_code)` | 行业研报 | 东财 |
| 2.2 | `ths_eps_forecast(code)` | 机构一致预期 EPS | 同花顺 |
| 2.3 | `iwencai_search(query)` / `iwencai_query(query)` | NL 语义搜研报/选股（需 Key） | iwencai |
| 7.1 | `cninfo_announcements(code)` | 公告检索+PDF 下载 | 巨潮 |
| 7.2 | `client.F10(symbol, name='最新提示')` | 最新公告摘要 | 通达信 |


完整可运行代码见 [reference-endpoints.md](reference-endpoints.md)。

