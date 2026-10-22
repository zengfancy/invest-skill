# us-stock-pulse 端点代码

## 6.1 相对强弱

```python
import yfinance as yf

def relative_strength(ticker: str, bench: str = "SPY", days: int = 60) -> dict:
    t = norm_us_ticker(ticker)
    b = norm_us_ticker(bench)
    yf_throttle()
    a = yf.Ticker(t).history(period=f"{max(days + 5, 30)}d")
    yf_throttle()
    s = yf.Ticker(b).history(period=f"{max(days + 5, 30)}d")
    if a.empty or s.empty:
        return {"error": "empty history"}
    a_ret = float(a["Close"].iloc[-1] / a["Close"].iloc[-min(days, len(a))] - 1)
    s_ret = float(s["Close"].iloc[-1] / s["Close"].iloc[-min(days, len(s))] - 1)
    return json_safe({
        "ticker": t,
        "bench": b,
        "days": days,
        "ticker_return": a_ret,
        "bench_return": s_ret,
        "excess_return": a_ret - s_ret,
    })
```

## 6.2 期权粗览

```python
def yahoo_options_iv_snapshot(ticker: str) -> dict:
    t = norm_us_ticker(ticker)
    yf_throttle()
    tk = yf.Ticker(t)
    dates = list(tk.options or [])
    if not dates:
        return {"error": "no options chain", "ticker": t}
    exp = dates[0]
    yf_throttle()
    chain = tk.option_chain(exp)
    calls = chain.calls
    puts = chain.puts
    def _iv_mean(df):
        if df is None or df.empty or "impliedVolatility" not in df.columns:
            return None
        return float(df["impliedVolatility"].dropna().mean())
    return json_safe({
        "expiry": exp,
        "n_calls": len(calls) if calls is not None else 0,
        "n_puts": len(puts) if puts is not None else 0,
        "call_iv_mean": _iv_mean(calls),
        "put_iv_mean": _iv_mean(puts),
    })
```
