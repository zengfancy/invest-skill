# us-stock-quote 端点代码

> 执行前先加载 `us-stock-core` helper。

## 1.1 批量行情快照

```python
import yfinance as yf

def yahoo_quote(tickers: list[str]) -> dict:
    """Return {ticker: {price, prev_close, pe_ttm, pb, mcap, ...}}."""
    out = {}
    for raw in tickers:
        t = norm_us_ticker(raw) if not str(raw).startswith("^") else str(raw)
        yf_throttle()
        tk = yf.Ticker(t)
        info = {}
        try:
            info = tk.fast_info.__dict__ if hasattr(tk, "fast_info") else {}
        except Exception:
            info = {}
        # fast_info may be object; also try .info sparingly (heavier)
        price = getattr(tk.fast_info, "last_price", None) if hasattr(tk, "fast_info") else None
        meta = {
            "ticker": t,
            "price": price,
            "prev_close": getattr(tk.fast_info, "previous_close", None) if hasattr(tk, "fast_info") else None,
            "mcap": getattr(tk.fast_info, "market_cap", None) if hasattr(tk, "fast_info") else None,
            "year_high": getattr(tk.fast_info, "year_high", None) if hasattr(tk, "fast_info") else None,
            "year_low": getattr(tk.fast_info, "year_low", None) if hasattr(tk, "fast_info") else None,
        }
        try:
            yf_throttle()
            full = tk.info or {}
            meta.update({
                "name": full.get("shortName") or full.get("longName"),
                "currency": full.get("currency"),
                "exchange": full.get("exchange"),
                "pe_ttm": full.get("trailingPE"),
                "pe_forward": full.get("forwardPE"),
                "pb": full.get("priceToBook"),
                "ps_ttm": full.get("priceToSalesTrailing12Months"),
                "eps_ttm": full.get("trailingEps"),
                "eps_forward": full.get("forwardEps"),
                "beta": full.get("beta"),
                "dividend_yield": full.get("dividendYield"),
            })
            if meta["price"] is None:
                meta["price"] = full.get("currentPrice") or full.get("regularMarketPrice")
            if meta["mcap"] is None:
                meta["mcap"] = full.get("marketCap")
        except Exception as e:
            meta["info_error"] = str(e)
        out[t] = json_safe(meta)
    return out
```

## 1.2 历史 K 线

```python
def yahoo_history(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """OHLCV history. period: 1mo/3mo/1y/2y/5y/max; interval: 1d/1wk/1mo."""
    t = norm_us_ticker(ticker) if not ticker.startswith("^") else ticker
    yf_throttle()
    df = yf.Ticker(t).history(period=period, interval=interval, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    return df
```

## 1.3 指数快照

```python
def yahoo_index_snapshot() -> dict:
    return yahoo_quote(["^GSPC", "^IXIC", "^DJI", "^VIX", "SPY", "QQQ"])
```
