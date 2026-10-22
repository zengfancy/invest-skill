# us-stock-research 端点代码

## 3.1 分析师摘要

```python
import yfinance as yf

def yahoo_analyst_summary(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    info = yf.Ticker(t).info or {}
    return json_safe({
        "recommendation": info.get("recommendationKey"),
        "recommendation_mean": info.get("recommendationMean"),
        "n_analysts": info.get("numberOfAnalystOpinions"),
        "target_mean": info.get("targetMeanPrice"),
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "target_median": info.get("targetMedianPrice"),
        "eps_current_year": info.get("epsCurrentYear"),
        "eps_forward": info.get("forwardEps"),
        "revenue_estimate": None,  # often not in info; leave gap
        "pe_forward": info.get("forwardPE"),
    })
```

## 3.2 财报日

```python
def yahoo_earnings_dates(ticker: str, limit: int = 12) -> list:
    t = norm_us_ticker(ticker)
    yf_throttle()
    df = yf.Ticker(t).earnings_dates
    if df is None or df.empty:
        return []
    df = df.reset_index().head(limit)
    return json_safe(df.to_dict(orient="records"))
```

## 3.3 Finnhub 评级（可选）

```python
def finnhub_recommendation(ticker: str) -> list:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        return [{"error": "FINNHUB_API_KEY not set"}]
    t = norm_us_ticker(ticker)
    r = yf_get(
        "https://finnhub.io/api/v1/stock/recommendation",
        params={"symbol": t, "token": key},
    )
    return r.json()
```
