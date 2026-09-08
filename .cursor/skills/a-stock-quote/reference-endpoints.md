# a-stock-quote 端点代码（Layer 1）

> 执行前先加载 `a-stock-core` 的 `tdx_client` / `norm_ticker`。

## Layer 1: 行情层（实时，不封IP）

### 1.1 mootdx — K线 + 五档盘口 + 逐笔成交

TCP 二进制协议，连通达信服务器(7709)，无需注册，不封IP。

```python
from mootdx.quotes import Quotes

client = tdx_client()  # 见 Prerequisites 的 tdx_client() helper（规避 0.11.x BESTIP bug；等价 Quotes.factory(market='std')）

# === K线数据 ===
# ⚠️ 参数名是 frequency（不是 category！传 category 会被 **kwargs 静默吞掉，
#    永远退化成默认 frequency=9 日线，拿不到分钟数据）。
# mootdx 0.11.7 实测频率值表：
#   0=5分钟  1=15分钟  2=30分钟  3=60分钟(1小时)  4=日线  5=周线  6=月线
#   8=1分钟  9=日线(默认)  10=季线  11=年线        （7=1分钟除权口径,少用）
klines = client.bars(symbol='688017', frequency=9, offset=10)    # 日线
min1   = client.bars(symbol='688017', frequency=8, offset=240)   # 1分钟（一个交易日≈240根）
min5   = client.bars(symbol='688017', frequency=0, offset=48)    # 5分钟
# 返回: open, close, high, low, vol, amount, datetime
# ⚠️ 复权：bars 返回【不复权】原始价（通达信原始数据，无 adjust 参数）。
#    跨除权除息日做估值/回测前需自行复权，或改用带前复权的日K数据源（腾讯财经）。

# === 实时报价 ===
quotes = client.quotes(symbol=['688017', '300476'])
# 返回 46 个字段:
#   price(现价), open, high, low, last_close(昨收)
#   bid1~bid5, ask1~ask5, bid_vol1~bid_vol5, ask_vol1~ask_vol5
#   vol(成交量), amount(成交额), servertime

# === 逐笔成交（非交易时间返回空）===
trades = client.transaction(symbol='688017', date='20260502')
# 返回: time, price, vol, num, buyorsell(0买/1卖/2中性)
```

**mootdx 不提供 PE / PB / 市值 / 换手率 / 涨跌停价** — 这些走腾讯财经。

### 1.2 腾讯财经 API — PE/PB/市值/换手率/涨跌停/指数/ETF

HTTP GET，GBK 编码，`~` 分隔 88 个字段，不封IP。

```python
import urllib.request

def tencent_quote(codes: list[str]) -> dict[str, dict]:
    """
    批量拉取腾讯财经实时行情。
    codes: ["688017", "300476", "002463"]
    也支持指数: ["000001", "000300", "399006"]
    也支持ETF: ["510050", "510300"]
    返回: {code: {name, price, pe_ttm, pb, mcap, ...}}
    """
    # 前缀路由：与全局 get_prefix() 一致。5x 沪ETF / 000300 等沪指数不能落到 sz（会返回空或错票）。
    SH_INDEX = {"000300", "000905", "000016", "000688", "000852", "000010"}   # 沪指数白名单
    prefixed = []
    key_of = {}          # 带前缀的查询键 → 调用方原始写法，保证结果键与入参一一对应
    for c in codes:
        low = c.lower()
        if low.startswith(("sh", "sz", "bj")):        # 显式前缀透传，解决 000001 等歧义
            p = low
        elif c.startswith("92"):                      # 北交所 920 号段须先于 9x 判断
            p = f"bj{c}"
        elif c in SH_INDEX or c.startswith(("5", "6", "9")):
            p = f"sh{c}"
        elif c.startswith(("4", "8")):
            p = f"bj{c}"
        else:
            p = f"sz{c}"
        prefixed.append(p)
        key_of[p] = c    # 显式前缀入参原样返回，裸代码返回裸代码

    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode("gbk")

    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        # 用入参原样做键：批量里同时传 sh000001 与 sz000001 时，若都退回裸 6 位码
        # 会撞成同一个键、后者静默覆盖前者，显式前缀这个特性就白做了。
        code = key_of.get(key, key[2:])
        result[code] = {
            "name":         vals[1],
            "price":        float(vals[3]) if vals[3] else 0,
            "last_close":   float(vals[4]) if vals[4] else 0,
            "open":         float(vals[5]) if vals[5] else 0,
            "change_amt":   float(vals[31]) if vals[31] else 0,
            "change_pct":   float(vals[32]) if vals[32] else 0,
            "high":         float(vals[33]) if vals[33] else 0,
            "low":          float(vals[34]) if vals[34] else 0,
            "amount_wan":   float(vals[37]) if vals[37] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "pe_ttm":       float(vals[39]) if vals[39] else 0,
            "amplitude_pct":float(vals[43]) if vals[43] else 0,
            # ⚠️ 44=流通市值、45=总市值（曾标反）。总股本≠流通股本时差数倍，见上方踩坑提醒二
            "float_mcap_yi":float(vals[44]) if vals[44] else 0,
            "mcap_yi":      float(vals[45]) if vals[45] else 0,
            "pb":           float(vals[46]) if vals[46] else 0,
            "limit_up":     float(vals[47]) if vals[47] else 0,
            "limit_down":   float(vals[48]) if vals[48] else 0,
            "vol_ratio":    float(vals[49]) if vals[49] else 0,
            "pe_static":    float(vals[52]) if vals[52] else 0,
        }
        # 僵尸报价检测：腾讯对「已迁移的北交所老码 / 长期停牌股」照样返回 HTTP 200 +
        # 一份定格在最后交易日的报价（成交量 0、最新价==昨收），不报任何错。
        # 直接拿去算估值会得出完全错误的结论（实测 bj832982 报 112.60，真实新码 920982 为 131.74）。
        q = result[code]
        q["is_stale"] = (q["amount_wan"] == 0 and q["price"] == q["last_close"] and q["price"] > 0)
        if q["is_stale"] and key[2:4] in ("43", "83", "87"):
            q["stale_reason"] = "北交所老号段，多数已迁至 920xxx，请按名称反查现行代码"
        elif q["is_stale"]:
            q["stale_reason"] = "成交量为 0（停牌 / 未开盘 / 废码），报价非当日真实成交"
    return result

# 用法: 个股
quotes = tencent_quote(["688017", "300476", "002463"])
for code, q in quotes.items():
    print(f"{q['name']}({code}): {q['price']}元 PE={q['pe_ttm']} PB={q['pb']} 市值={q['mcap_yi']}亿")

# 用法: 指数 — sh000001=上证指数, sh000300=沪深300, sz399006=创业板指
index_quotes = tencent_quote(["000001", "000300", "399006"])

# 用法: ETF — sh510050=上证50ETF, sh510300=沪深300ETF
etf_quotes = tencent_quote(["510050", "510300"])
```

#### 腾讯财经字段索引速查（实测校准 2026-05-03）

| 索引 | 含义 | 示例 |
|------|------|------|
| 1 | 名称 | 绿的谐波 |
| 3 | 当前价 | 224.12 |
| 4 | 昨收 | 215.01 |
| 5 | 今开 | 214.10 |
| 9-18 | 买一~买五(价+量) | |
| 19-28 | 卖一~卖五(价+量) | |
| 31 | 涨跌额 | 9.11 |
| 32 | 涨跌幅% | 4.24 |
| 33 | 最高 | 229.62 |
| 34 | 最低 | 214.10 |
| 37 | 成交额(万) | 187040 |
| 38 | 换手率% | 4.55 |
| **39** | **PE(TTM)** | 300.45 |
| **43** | **振幅%（不是PB！）** | 7.22 |
| **44** | **流通市值(亿)** | 410.88 |
| **45** | **总市值(亿)** | 410.88 |
| **46** | **PB(市净率)** | 11.51 |
| **47** | **涨停价** | 258.01 |
| **48** | **跌停价** | 172.01 |
| 49 | 量比 | 1.20 |
| **52** | **PE(静)** | 314.76 |

> **踩坑提醒一：** 网上很多教程把索引 43 写成 PB，实测是振幅%。PB 在索引 46。
>
> **踩坑提醒二（2026-07-26 修正）：** **44 是流通市值、45 才是总市值**，此前本表标反了。
> 多数股票两者相等，所以看不出来；但**总股本 ≠ 流通股本的票（科创板/次新股/有限售股）会差出数倍**。
> 实测中船特气(688146)：`f[44]=356.15亿`(流通股本 1.45亿股)、`f[45]=1300.61亿`(总股本 5.29亿股)，**差 3.65 倍**。
> 用市值做筛选时取错会把大市值公司误判成小盘股。可用 `f[45] ÷ 现价` 反推总股本核对（与东财 `f84` 一致）。
> 参考：东财 push2 的 `f116`=总市值 / `f117`=流通市值 方向与腾讯相反，实测确认无误，勿混用。

### 1.3 百度股市通 K线 — 带MA5/MA10/MA20（V3.0 新增）

**核心价值：** 返回时自带均线数据，无需本地计算。

```python
import requests

def baidu_kline_with_ma(code: str, start_time: str = "") -> dict:
    """百度股市通K线 — 独有能力: 返回时自带 ma5/ma10/ma20 均价"""
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {
        "all": "1", "isIndex": "false", "isBk": "false", "isBlock": "false",
        "isFutures": "false", "isStock": "true", "newFormat": "1",
        "group": "quotation_kline_ab", "finClientType": "pc",
        "code": code, "start_time": start_time, "ktype": "1",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    d = r.json()
    result = d.get("Result", {})
    md = result.get("newMarketData", {})
    keys = md.get("keys", [])  # includes: ma5avgprice, ma10avgprice, ma20avgprice
    rows = md.get("marketData", "").split(";")
    return {"keys": keys, "rows": rows}

# 用法
data = baidu_kline_with_ma("600519")
print("字段:", data["keys"][:10])
print("最近5根K线:", data["rows"][-5:])
# keys 包含: time, open, close, high, low, volume, amount, ma5avgprice, ma10avgprice, ma20avgprice 等
```

---

### 1.4 新浪复权因子 — qfq / hfq（V3.7.0 新增）

**核心价值：** §1.1 `tdx_client().bars()` 返回的是**不复权**数据，跨除权日直接比价必然出错。
本端点给出复权因子序列，一次 HTTP、约 1.8KB、零鉴权。

```python
import json
import re

import requests

def sina_adjust_factor(code: str, kind: str = "qfq") -> list:
    """新浪复权因子序列 — kind='qfq'(前复权) | 'hfq'(后复权)，按日期倒序（最新在前）"""
    if kind not in ("qfq", "hfq"):
        raise ValueError(f"kind 只能是 'qfq' 或 'hfq'，收到 {kind!r}")
    # 数字位用 norm_ticker() 剥掉前后缀（否则 "sz000016" 会拼成 "szsz000016" ——
    # zfill(6) 对 8 字符输入不做任何事）。
    raw = str(code).strip()
    digits = norm_ticker(raw)
    # 市场：**显式写法优先**——前缀或 `.SH` 后缀直接采信（V3.7.1 起 get_prefix() 也认后缀，
    # 本地显式匹配保留，语义不变）。都没写显式市场时，才用 get_prefix() 按号段推断
    # （它已处理 92 必须先于 9x）。
    m = re.match(r"^(sh|sz|bj)", raw, re.I) or re.search(r"\.(sh|sz|bj)$", raw, re.I)
    prefix = m.group(1).lower() if m else get_prefix(digits)
    symbol = f"{prefix}{digits}"
    url = f"https://finance.sina.com.cn/realstock/company/{symbol}/{kind}.js"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0",
                                   "Referer": "https://finance.sina.com.cn/"}, timeout=10)
    r.raise_for_status()
    # 🔴 响应形如 `var sh600519qfq={...}` 且**末尾挂着 /* base64 */ 注释块**，
    #    不能用 $ 锚定正则。从第一个 { 起用 raw_decode，让解析器自己在 JSON 结束处停下。
    text = r.text
    brace = text.find("{")
    if brace < 0:
        raise RuntimeError(f"新浪复权因子响应无 JSON（{symbol}/{kind}）: {text[:120]}")
    try:
        data, _ = json.JSONDecoder().raw_decode(text[brace:])
    except json.JSONDecodeError as e:
        raise RuntimeError(f"新浪复权因子 JSON 解析失败（{symbol}/{kind}）: {e}") from e
    return [{"date": it["d"], "factor": float(it["f"])} for it in data.get("data", [])]

def apply_adjust(bars, factors: list, kind: str = "qfq",
                 price_keys=("open", "high", "low", "close")):
    """把复权因子套到不复权 K 线上。

    `bars` 接受两种形态：
      - **§1.1 `tdx_client().bars()` 的 DataFrame**（日期列名是 `datetime`）→ 返回 DataFrame
      - list[dict]（需含 `date` 键）→ 返回 list[dict]

    🔴 **qfq 与 hfq 的运算方向相反，必须传对 kind**：
      - `qfq`（前复权）因子是**除数**：`前复权价 = 不复权价 ÷ factor`
      - `hfq`（后复权）因子是**乘数**：`后复权价 = 不复权价 × factor`
    传错方向不会报错，只会把历史价格放大/缩小几倍（见下方实测对照表）。

    因子表是「生效日 → 因子」的阶梯，每根 K 线取**不晚于它**的最近一个因子。
    """
    if kind not in ("qfq", "hfq"):
        raise ValueError(f"kind 只能是 'qfq' 或 'hfq'，收到 {kind!r}")
    # 🔴 因子为空时绝不能「原样返回」—— 那会把不复权价当成复权价交出去，
    #    调用方拿到的数字看着正常却是错的（新浪对不支持的标的就返回空 data）。
    if not factors:
        raise ValueError(
            "复权因子列表为空，无法复权。请先确认 sina_adjust_factor() 是否取到数据"
            "（新浪对不支持的标的会返回空 data），不要用未复权价继续计算。"
        )

    is_df = hasattr(bars, "columns") and hasattr(bars, "to_dict")
    if is_df:
        # mootdx bars() 的日期列叫 datetime，且可能带时分秒，统一截成 YYYY-MM-DD
        date_col = next((c for c in ("date", "datetime") if c in bars.columns), None)
        if date_col is None:
            raise ValueError(f"DataFrame 需含 date 或 datetime 列，实际列={list(bars.columns)}")
        rows = bars.to_dict("records")
        for r in rows:
            r["date"] = str(r[date_col])[:10]
    else:
        rows = [dict(b) for b in bars]
        for r in rows:
            if "date" not in r:
                raise ValueError(f"每根 K 线需含 'date' 键，实际键={sorted(r)}")
            r["date"] = str(r["date"])[:10]

    fac = sorted(factors, key=lambda x: x["date"])
    out, i, cur = [], 0, None
    for bar in sorted(rows, key=lambda b: b["date"]):
        while i < len(fac) and fac[i]["date"] <= bar["date"]:
            cur = fac[i]["factor"]
            i += 1
        # 🔴 早于最早因子日的 K 线不能原样放行 —— 那会让一份结果里混着「已复权」和
        #    「未复权」两种价格且无从分辨。新浪的因子表通常带 1900-01-01 哨兵
        #    （实测 600519/000001/300750/688981/000004/601398 六只均是），
        #    真出现未覆盖行，说明因子表异常，必须显式失败。
        if cur is None:
            raise RuntimeError(
                f"K 线日期 {bar['date']} 早于因子序列最早日 {fac[0]['date']}，"
                "无法复权；不返回未复权价以免与已复权行混淆。"
            )
        if cur == 0:
            raise RuntimeError(f"复权因子为 0（{bar['date']}），无法换算")
        nb = dict(bar)
        for k in price_keys:
            if k in nb and nb[k] is not None:
                v = float(nb[k])
                nb[k] = round(v / cur if kind == "qfq" else v * cur, 4)
        nb["adj_factor"] = cur
        out.append(nb)
    if is_df:
        import pandas as pd
        res = pd.DataFrame(out)
        # mootdx 的 bars() 带 DatetimeIndex，重建 DataFrame 会退化成 RangeIndex，
        # 下游按时间切片 / resample / 时间对齐 join 都会失效。按排序后的顺序还原索引。
        if getattr(bars, "index", None) is not None and not isinstance(
            bars.index, pd.RangeIndex
        ):
            order = sorted(range(len(bars)), key=lambda n: str(bars.iloc[n][date_col])[:10])
            res.index = bars.index[order]
            res.index.name = bars.index.name
        return res
    return out

# 用法
qfq = sina_adjust_factor("600519", "qfq")
hfq = sina_adjust_factor("600519", "hfq")
print(len(qfq), "条 | 最新", qfq[0], "| 最早", qfq[-1])
# 实测 2026-08-19：33 条
#   qfq 最新 {'date': '2026-06-26', 'factor': 1.0}          ← 前复权以最新为基准
#   hfq 最早 {'date': '1900-01-01', 'factor': 1.0}          ← 后复权以最早为基准

bars = [{"date": "2015-01-05", "close": 202.52}]         # 茅台当日不复权收盘价
print(apply_adjust(bars, qfq, kind="qfq"))                # → 143.46（前复权，除法）
print(apply_adjust(bars, hfq, kind="hfq"))                # → 1274.28（后复权，乘法）
```

**方向实测对照（2026-08-19，以 baostock `adjustflag` 为基准交叉验证）**

| 日期 | 不复权 | baostock 前复权 | `raw × qfq` | `raw ÷ qfq` |
|------|--------|----------------|-------------|-------------|
| 2015-01-05 | 202.52 | **143.46** | 285.90 ❌ | **143.46** ✅ |
| 2026-08-14 | 1341.99 | 1341.99 | 1341.99 ✅ | 1341.99 ✅ |

> `qfq` 因子恒 ≥ 1 且越往历史越大，**乘上去会把历史价格放大**，必须做除法。
> 2026 那行两种算法都对，是因为最新日因子恰为 1.0 —— **只用最近日期做验证会漏掉这个 bug**。
>
> ⚠️ **hfq 的基准与 baostock 不同**：新浪 `raw × hfq` 与 baostock 后复权价差一个**恒定倍数**
> （实测 1.1582，2015 与 2026 两点一致）。后复权序列整体缩放不影响收益率与形态，
> 但**不要把新浪后复权价与其它源的后复权价直接比数值**。

> ⚠️ **北交所无复权因子**：实测 `bj920982` 返回 **404**（新浪未提供北交所的 qfq/hfq 文件），
> 本函数会抛 `HTTPError`。北交所标的请改用 §1.1 通达信不复权价，并自行按分红送转推导。
>
> **自检口径（实测 2026-08-19 校准）：**
> - `qfq` 序列**最新**一条因子恒为 `1.0`；`hfq` 序列**最早**一条恒为 `1.0`。
> - 同一日期上 **`qfq(d) × hfq(d)` 恒等于一个常数**（该标的全期总复权系数，茅台实测 `8.882513`）。
> ⚠️ 两者**不是倒数**（乘积不为 1），比值 `hfq/qfq` 也**不恒定**（茅台 33 个日期有 32 种取值）——
> 两个基准不同的归一化序列，只有乘积守恒。
> 不满足以上任一条，说明响应被截断或标的代码写错。

---


