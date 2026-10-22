# us-stock-fundamentals 端点代码

> 执行前加载 `us-stock-core`。

## 2.1 三表

```python
import yfinance as yf

def yahoo_financials(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    tk = yf.Ticker(t)
    out = {}
    for name, getter in [
        ("income_annual", lambda: tk.incomestmt),
        ("income_quarterly", lambda: tk.quarterly_incomestmt),
        ("balance_annual", lambda: tk.balance_sheet),
        ("balance_quarterly", lambda: tk.quarterly_balance_sheet),
        ("cash_annual", lambda: tk.cashflow),
        ("cash_quarterly", lambda: tk.quarterly_cashflow),
    ]:
        try:
            yf_throttle()
            df = getter()
            if df is None or df.empty:
                out[name] = []
            else:
                out[name] = json_safe(df.reset_index().to_dict(orient="records"))
        except Exception as e:
            out[name] = {"error": str(e)}
    return out
```

## 2.2 关键倍数与质量线索

```python
def yahoo_key_metrics(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    info = yf.Ticker(t).info or {}
    keys = [
        "symbol", "shortName", "sector", "industry", "currency",
        "marketCap", "enterpriseValue", "trailingPE", "forwardPE",
        "priceToBook", "priceToSalesTrailing12Months", "enterpriseToEbitda",
        "profitMargins", "grossMargins", "operatingMargins",
        "returnOnEquity", "returnOnAssets", "freeCashflow", "operatingCashflow",
        "totalCash", "totalDebt", "debtToEquity",
        "revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth",
        "sharesOutstanding", "floatShares", "heldPercentInstitutions",
        "trailingEps", "forwardEps", "bookValue",
        "dividendYield", "payoutRatio", "recommendationKey", "targetMeanPrice",
    ]
    return json_safe({k: info.get(k) for k in keys})
```

## 2.3 盈利预期摘要

```python
def yahoo_earnings_trend(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    tk = yf.Ticker(t)
    out = {}
    try:
        out["earnings_dates"] = json_safe(tk.earnings_dates.reset_index().to_dict(orient="records")) if tk.earnings_dates is not None else []
    except Exception as e:
        out["earnings_dates"] = {"error": str(e)}
    try:
        cal = tk.calendar
        out["calendar"] = json_safe(cal if isinstance(cal, dict) else getattr(cal, "to_dict", lambda: {})())
    except Exception as e:
        out["calendar"] = {"error": str(e)}
    return out
```

## 2.4 SEC CIK 与近期申报

```python
def sec_company_tickers() -> dict:
    """Map ticker → CIK. Cached by caller if needed."""
    r = sec_get("https://www.sec.gov/files/company_tickers.json")
    data = r.json()
    # { "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ... }
    by_ticker = {}
    for row in data.values():
        by_ticker[str(row["ticker"]).upper()] = {
            "cik": int(row["cik_str"]),
            "cik_str": str(row["cik_str"]).zfill(10),
            "title": row["title"],
        }
    return by_ticker


def sec_recent_filings(ticker: str, count: int = 20) -> list:
    t = norm_us_ticker(ticker)
    mapping = sec_company_tickers()
    if t not in mapping:
        return [{"error": f"CIK not found for {t}"}]
    cik = mapping[t]["cik_str"]
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = sec_get(url)
    j = r.json()
    recent = j.get("filings", {}).get("recent", {})
    rows = []
    n = len(recent.get("accessionNumber", []))
    for i in range(min(count, n)):
        rows.append({
            "form": recent["form"][i],
            "filingDate": recent["filingDate"][i],
            "accessionNumber": recent["accessionNumber"][i],
            "primaryDocument": recent["primaryDocument"][i],
            "reportUrl": (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{recent['accessionNumber'][i].replace('-', '')}/"
                f"{recent['primaryDocument'][i]}"
            ),
        })
    return rows
```

## 估值小公式

```python
def forward_pe(price: float, eps_forward: float) -> float | None:
    if not price or not eps_forward or eps_forward <= 0:
        return None
    return price / eps_forward


def calc_peg(pe: float, growth_pct: float) -> float | None:
    """growth_pct: e.g. 18 for 18% CAGR. PEG = PE / growth."""
    if not pe or not growth_pct or growth_pct <= 0:
        return None
    return pe / growth_pct
```
