---
name: us-stock-core
description: >-
  美股取数共用底座：ticker归一化(norm_us_ticker)、Yahoo限流(yf_get)、SEC UA、
  数据源优先级与防封、pip依赖、上市地/ADR注意点。在调用任何 us-stock-* 场景
  skill 的 Yahoo/SEC/Finnhub 端点之前必须先加载本 skill。
origin: custom
version: 1.0.0
---

# 美股取数共用底座（us-stock-core）

所有场景 skill（quote / fundamentals / research / pulse / capital / macro）共享本文件 helper。  
**先执行本文代码块，再执行场景 `reference-endpoints.md` 中的端点代码。**

## 端点总路由

| 场景 skill | 覆盖 | 详见 |
|---|---|---|
| [`us-stock-quote`](../us-stock-quote/SKILL.md) | 现价 / K线 / 市值 / 指数 | Layer 1 |
| [`us-stock-fundamentals`](../us-stock-fundamentals/SKILL.md) | 三表 / 分部 / 估值历史 / Non-GAAP | Layer 2 |
| [`us-stock-research`](../us-stock-research/SKILL.md) | 一致预期 / 评级 / 指引 / 电话会摘要 | Layer 3 |
| [`us-stock-macro`](../us-stock-macro/SKILL.md) | 公司新闻 / 宏观 (FRED) / 财报日历 | Layer 4 |
| [`us-stock-capital`](../us-stock-capital/SKILL.md) | 13F / Form 4 / 回购 / 分红 | Layer 5 |
| [`us-stock-pulse`](../us-stock-pulse/SKILL.md) | 短兴趣 / 期权概览 / 异动热度 | Layer 6 |
| [`us-stock-data`](../us-stock-data/SKILL.md) | 薄路由总索引 | — |

## 数据源优先级 & 防封

### 优先级原则：能用免费公开源就不用付费 Key

| 优先级 | 数据源 | 封 IP / 限流 | 覆盖 |
|--------|--------|--------------|------|
| **1（首选）** | **yfinance / Yahoo chart** | 有限流，通常不永久封 | 行情、K线、基本面摘要、期权链粗数据 |
| **2** | **SEC EDGAR** | 要求 UA；QPS 宜 ≤10 | 10-K/10-Q/8-K、Form 4、13F 入口 |
| **3** | **FRED** | 可选 API Key；公开亦可部分拉 | 利率、CPI、就业等宏观 |
| **4（可选）** | **Finnhub / Polygon** | 需 API Key | 新闻、一致预期、更高频行情 |

**铁律：**

1. 串行调用 Yahoo；批量间隔 ≥ 0.3–0.5s + 抖动  
2. SEC 请求必须带可识别 `User-Agent`（含联系邮箱，否则易 403）  
3. 禁止臆造财报数字；取不到写「未取得」  
4. **GAAP vs Non-GAAP 必须分列**，禁止混用  
5. 中概 ADR（BABA、PDD 等）报价走本套；年报以 20-F / 港股年报为准时在报告中注明  

## Prerequisites

```bash
pip install yfinance requests pandas numpy
# 可选：
# pip install fredapi finnhub-python
```

环境变量（可选）：

| 变量 | 用途 |
|------|------|
| `SEC_USER_AGENT` | 例：`YourName your@email.com` |
| `FINNHUB_API_KEY` | 新闻/预期增强 |
| `FRED_API_KEY` | 宏观增强 |
| `POLYGON_API_KEY` | 行情备胎 |

## 共用 helper（执行场景端点前必跑）

```python
from __future__ import annotations

import os
import random
import re
import time
from typing import Optional

import pandas as pd
import requests

UA = os.environ.get(
    "SEC_USER_AGENT",
    "invest-skill research bot contact@example.com",
)
YF_MIN_INTERVAL = 0.4
_yf_last = [0.0]

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9",
})

_TICKER_RE = re.compile(
    r"^(?:([A-Za-z]{1,6})(?:[.\-]([A-Za-z]))?)$"
)


def norm_us_ticker(code: str) -> str:
    """Normalize US ticker.
    AAPL / aapl / BRK.B / BRK-B / brk.b → canonical Yahoo form (BRK-B).
    Raises ValueError on empty/invalid.
    """
    raw = str(code).strip().upper()
    if not raw:
        raise ValueError("empty ticker")
    # strip exchange suffixes like AAPL.US / NYSE:AAPL
    raw = raw.replace("NYSE:", "").replace("NASDAQ:", "").replace("AMEX:", "")
    if raw.endswith(".US"):
        raw = raw[:-3]
    raw = raw.replace(".", "-")  # Yahoo uses BRK-B
    if not re.fullmatch(r"[A-Z]{1,5}(?:-[A-Z])?", raw) and not re.fullmatch(r"[A-Z]{1,6}", raw):
        # allow up to 5 + optional class, or ETFs like BRK-B already handled
        if not re.fullmatch(r"[A-Z0-9.\-]{1,10}", raw):
            raise ValueError(f"无法解析美股代码: {code!r}")
    return raw


def yf_throttle():
    wait = YF_MIN_INTERVAL - (time.time() - _yf_last[0])
    if wait > 0:
        time.sleep(wait + random.uniform(0.05, 0.25))
    _yf_last[0] = time.time()


def yf_get(url: str, params: Optional[dict] = None, timeout: int = 20):
    """Throttled GET for Yahoo / generic JSON APIs."""
    yf_throttle()
    r = SESSION.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r


def sec_get(url: str, params: Optional[dict] = None, timeout: int = 30):
    """SEC EDGAR GET with required User-Agent."""
    yf_throttle()
    headers = {"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}
    r = SESSION.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(x) for x in obj]
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass
    if hasattr(obj, "item"):
        try:
            return json_safe(obj.item())
        except Exception:
            return str(obj)
    return obj
```

## 与投研 skill 的衔接

做美股深度报告时：

1. 取数走 `us-stock-*`（本套）  
2. 方法论仍用 [`value-leader-research`](../value-leader-research/SKILL.md) / [`growth-tech-research`](../growth-tech-research/SKILL.md) / [`platform-leader-research`](../platform-leader-research/SKILL.md)  
3. 落盘：`reports/{TICKER}-{简称}/`（例：`reports/AAPL-苹果/`）  
4. 总览元信息写明：`市场 US` + 框架名  

港股平台巨头继续用 `platform-leader` + 港股 IR，**不要**硬套本套 Yahoo 三表代替年报分部。
