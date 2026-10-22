# us-stock-capital 端点代码

## 5.1 持股摘要

```python
import yfinance as yf

def yahoo_holders_summary(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    info = yf.Ticker(t).info or {}
    return json_safe({
        "heldPercentInstitutions": info.get("heldPercentInstitutions"),
        "heldPercentInsiders": info.get("heldPercentInsiders"),
        "floatShares": info.get("floatShares"),
        "sharesOutstanding": info.get("sharesOutstanding"),
        "dividendYield": info.get("dividendYield"),
        "payoutRatio": info.get("payoutRatio"),
        "lastDividendValue": info.get("lastDividendValue"),
    })
```

## 5.2 内部人交易

```python
def yahoo_insider_transactions(ticker: str) -> list:
    t = norm_us_ticker(ticker)
    yf_throttle()
    df = yf.Ticker(t).insider_transactions
    if df is None or (hasattr(df, "empty") and df.empty):
        return []
    return json_safe(df.reset_index().head(50).to_dict(orient="records"))
```

## 5.3 Form 4 入口

```python
def sec_form4_filings(ticker: str, limit: int = 15) -> list:
    """Filter recent SEC filings for Form 4. Requires fundamentals sec helpers loaded or inline."""
    # reuse sec_recent_filings from fundamentals if available; else minimal copy
    from copy import deepcopy  # noqa — agent should paste sec_recent_filings if not in scope
    rows = sec_recent_filings(ticker, count=80)  # defined in us-stock-fundamentals
    if rows and isinstance(rows[0], dict) and rows[0].get("error"):
        return rows
    return [r for r in rows if str(r.get("form", "")).startswith("4")][:limit]
```
