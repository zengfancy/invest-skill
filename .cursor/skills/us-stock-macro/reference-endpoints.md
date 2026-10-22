# us-stock-macro 端点代码

## 4.1 Yahoo 个股新闻

```python
import yfinance as yf

def yahoo_news(ticker: str, limit: int = 30) -> list:
    t = norm_us_ticker(ticker)
    yf_throttle()
    items = yf.Ticker(t).news or []
    rows = []
    for it in items[:limit]:
        # yfinance news schema varies by version
        content = it.get("content") if isinstance(it.get("content"), dict) else {}
        rows.append({
            "title": it.get("title") or content.get("title"),
            "publisher": it.get("publisher") or content.get("provider", {}).get("displayName") if isinstance(content.get("provider"), dict) else it.get("publisher"),
            "link": it.get("link") or content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else it.get("link"),
            "providerPublishTime": it.get("providerPublishTime") or content.get("pubDate"),
        })
    return json_safe(rows)
```

## 4.2 Finnhub 新闻（可选）

```python
from datetime import date, timedelta

def finnhub_company_news(ticker: str, days: int = 14) -> list:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        return [{"error": "FINNHUB_API_KEY not set"}]
    t = norm_us_ticker(ticker)
    to = date.today()
    frm = to - timedelta(days=days)
    r = yf_get(
        "https://finnhub.io/api/v1/company-news",
        params={"symbol": t, "from": frm.isoformat(), "to": to.isoformat(), "token": key},
    )
    return r.json()
```

## 4.3 FRED 宏观序列

常用 series：`FEDFUNDS`、`CPIAUCSL`、`UNRATE`、`DGS10`、`T10Y2Y`。

```python
def fred_series(series_id: str, limit: int = 120) -> list:
    """Fetch observations. Uses FRED_API_KEY if set; else public graph JSON may fail — prefer API."""
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return [{"error": "FRED_API_KEY not set", "hint": "https://fred.stlouisfed.org/docs/api/api_key.html"}]
    r = yf_get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": str(limit),
        },
    )
    return r.json().get("observations", [])
```
