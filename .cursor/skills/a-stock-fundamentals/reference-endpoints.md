# a-stock-fundamentals 端点代码（Layer 6 + 估值公式）

## Layer 6: 基础数据层

### 6.1 mootdx 财务快照（37字段季报数据）

```python
from mootdx.quotes import Quotes

client = tdx_client()  # 见 Prerequisites 的 tdx_client() helper（规避 0.11.x BESTIP bug；等价 Quotes.factory(market='std')）

# market: 0=深圳, 1=上海
fin = client.finance(symbol='688017')
# 返回 37 个字段的季报快照:
#   liutongguben(流通股本), zongguben(总股本)
#   eps(每股收益), bvps(每股净资产), roe(净资产收益率%)
#   profit(净利润), income(主营收入)
#   meigujingzichan(每股净资产), meigugongjijin(每股公积金)
#   meiguweifeipeili(每股未分配利润)
#   等37个季报财务字段
```

### 6.2 mootdx F10（公司文本资料）

```python
from mootdx.quotes import Quotes

client = tdx_client()  # 见 Prerequisites 的 tdx_client() helper（规避 0.11.x BESTIP bug；等价 Quotes.factory(market='std')）

# 9 大类文本数据:
categories = [
    "最新提示", "公司概况", "财务分析",
    "股东研究", "股本结构", "资本运作",
    "业内点评", "行业分析", "公司大事",
]
for cat in categories:
    text = client.F10(symbol='688017', name=cat)
    print(f"=== {cat} ===")
    print(text[:200] if text else "(空)")
```

> **优化提示：** "股东研究" 中的【4.股东变化】章节含大量历史十大股东列表，实测 16000+ chars。建议只保留最新一期（-70% token）。

### 6.3 东财个股基本面（直连 push2 API）

```python
import requests

def eastmoney_stock_info(code: str) -> dict:
    """
    东财个股基本面信息。
    返回: {code, name, industry, total_shares, float_shares, mcap, float_mcap, list_date}
    """
    market_code = em_market_code(code)      # #46
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "fltt": "2", "invt": "2",
        "fields": "f57,f58,f84,f85,f127,f116,f117,f189,f43",
        "secid": f"{market_code}.{code}",
    }
    headers = {"User-Agent": UA}
    r = em_get(url, params=params, headers=headers, timeout=10)
    d = r.json().get("data", {})
    return {
        "code": d.get("f57", ""),
        "name": d.get("f58", ""),
        "industry": d.get("f127", ""),
        "total_shares": d.get("f84", 0),     # 总股本(股)
        "float_shares": d.get("f85", 0),     # 流通股(股)
        "mcap": d.get("f116", 0),            # 总市值(元)
        "float_mcap": d.get("f117", 0),      # 流通市值(元)
        "list_date": str(d.get("f189", "")), # 上市日期 YYYYMMDD
        "price": d.get("f43", 0),
    }

# 用法
info = eastmoney_stock_info("688017")
print(f"{info['name']}({info['code']}): 行业={info['industry']} 总市值={info['mcap']/1e8:.0f}亿 上市={info['list_date']}")
```

### 6.4 新浪财报三表（资产负债表/利润表/现金流量表）

```python
import requests

def sina_financial_report(code: str, report_type: str = "lrb", num: int = 8) -> list[dict]:
    """
    新浪财报三表。
    code: 6位代码
    report_type: "fzb"(资产负债表) / "lrb"(利润表) / "llb"(现金流量表)
    num: 取最近 N 期（默认 8 期）
    返回: 按报告期倒序的记录列表，每期一条 dict：
          {"报告期": "2026-03-31", "<科目>": "<值>", "<科目>_同比": <同比>, ...}
          （item_value 为新浪原始字符串数值，仅在有同比时附 "_同比" 键）
    """
    prefix = get_prefix(code)               # #46：51x/588x/900x 也是沪市
    paper_code = f"{prefix}{code}"
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"
    params = {
        "paperCode": paper_code,
        "source": report_type,
        "type": "0",
        "page": "1",
        "num": str(num),
    }
    headers = {"User-Agent": UA}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    # 新浪实际结构: result.data.report_list 是「按报告期(如 '20260331')为键」的 dict,
    # 每期对象的 data 字段才是行项列表 [{item_title, item_value, item_tongbi}]。
    # #46 同因：任一层为 null 时 `.get(k, {})` 返回 None，链式 .get 会 AttributeError
    _j = r.json() or {}
    report_list = ((_j.get("result") or {}).get("data") or {}).get("report_list") or {}

    rows = []
    for period in sorted(report_list.keys(), reverse=True)[:num]:
        obj = report_list[period]
        rec = {"报告期": f"{period[:4]}-{period[4:6]}-{period[6:8]}"}
        for it in obj.get("data", []) or []:
            title = it.get("item_title", "")
            if not title or it.get("item_value") is None:
                continue
            rec[title] = it.get("item_value")
            tongbi = it.get("item_tongbi")
            if tongbi not in (None, ""):
                rec[title + "_同比"] = tongbi
        rows.append(rec)
    return rows

# 用法: 利润表
lrb = sina_financial_report("600519", "lrb")
for item in lrb[:3]:
    print(f"报告期: {item.get('报告期', '')} 净利润: {item.get('净利润', '')}")

# 用法: 资产负债表
fzb = sina_financial_report("600519", "fzb")

# 用法: 现金流量表
llb = sina_financial_report("600519", "llb")
```

---

### 6.5 baostock 估值历史 — PE/PB/PS/PCF + 换手率 + 停牌 + ST（V3.7.0 新增）

**核心价值：** §1.2 腾讯只给**当日**估值快照，本端点给**日频历史序列**（可回溯至 2016），
一次调用同时拿到四个我们此前完全没有的字段：**换手率**（筹码分布的必需输入）、
**停牌状态**、**ST 标记**、**历史估值**。

🔴 **北交所不支持**：baostock 服务端直接拒绝 4/8/92/920 号段，报
`10004011 股票代码未标识sh或sz`（2026-08-19 实测）。本实现在**登录前**就拦掉并抛 `ValueError`，
不浪费一次会话，也不会静默返回空表。

```python
from contextlib import contextmanager

import baostock as bs
import pandas as pd

@contextmanager
def bs_session():
    """baostock 登录会话 — 必须用上下文管理器，异常路径也保证 logout"""
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock 登录失败: {lg.error_code} {lg.error_msg}")
    try:
        yield
    finally:
        bs.logout()

def _rs_to_df(rs) -> pd.DataFrame:
    """baostock ResultData → DataFrame；错误码转异常，绝不静默返回空表"""
    if rs.error_code != "0":
        raise RuntimeError(f"baostock 查询失败: {rs.error_code} {rs.error_msg}")
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    return pd.DataFrame(rows, columns=rs.fields)

def _bs_code(code: str) -> str:
    """6位代码 → baostock 格式；北交所在登录前就拦掉"""
    code = str(code).zfill(6)
    if code[:2] in ("60", "68", "90"):
        return f"sh.{code}"
    if code[:2] in ("00", "30", "20"):
        return f"sz.{code}"
    raise ValueError(
        f"baostock 不支持该代码: {code}（北交所 4/8/92/920 号段会被服务端拒绝，"
        f"报 10004011 股票代码未标识sh或sz）。北交所估值请改用 §1.2 腾讯当日快照。"
    )

def baostock_valuation_history(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """估值历史序列 — PE/PB/PS/PCF + 换手率 + 停牌 + ST，日频"""
    bs_code = _bs_code(code)          # 先校验，失败就不必登录
    fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM,turn,tradestatus,isST"
    with bs_session():
        rs = bs.query_history_k_data_plus(
            bs_code, fields, start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="3",     # 3=不复权，与 §1.1 通达信口径一致
        )
        df = _rs_to_df(rs)
    for c in ("close", "peTTM", "pbMRQ", "psTTM", "pcfNcfTTM", "turn"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# 用法
df = baostock_valuation_history("600519", "2016-01-04", "2026-08-18")
print(len(df), "行", df.iloc[0]["date"], "→", df.iloc[-1]["date"])
print(df.tail(2)[["date", "close", "peTTM", "pbMRQ", "psTTM", "turn", "isST"]].to_string(index=False))
# 实测 2026-08-19：2581 行；2026-08-18 peTTM=19.93 pbMRQ=6.46 psTTM=9.37 turn=0.3098

# ST 标记实测有效：000004 在 2024-01 至今的 610 个交易日里有 276 天 isST=1
st = baostock_valuation_history("000004", "2024-01-01", "2026-08-18")
print("isST 分布:", st["isST"].value_counts().to_dict())     # {'0': 334, '1': 276}

# 停牌：tradestatus == "0"
print("停牌天数:", (df["tradestatus"] == "0").sum())
```

**字段说明**

| 字段 | 含义 | 备注 |
|------|------|------|
| `peTTM` `pbMRQ` `psTTM` `pcfNcfTTM` | 市盈率TTM / 市净率MRQ / 市销率TTM / 市现率TTM | 负值代表亏损，不要直接排序 |
| `turn` | 换手率（**百分数**，0.31 = 0.31%） | §4.6 筹码分布的必需输入 |
| `tradestatus` | `1`=正常交易 `0`=停牌 | 算指标前应过滤掉停牌日 |
| `isST` | `1`=ST/*ST `0`=正常 | 历史逐日标记，可还原「当时是不是 ST」 |

---

### 6.6 baostock 标的基本信息 — 上市日 / 退市日 / 状态（V3.7.0 新增）

**核心价值：** 唯一能拿到**退市日期**的零鉴权源。配合 §1.2 的 `is_stale` 僵尸报价标志，
可以在回测/筛选阶段直接剔除已退市标的。

```python
def baostock_stock_basic(code: str) -> dict:
    """标的基本信息 — ipoDate(上市日) / outDate(退市日，在市为空) / status(1=上市 0=退市)"""
    bs_code = _bs_code(code)
    with bs_session():
        df = _rs_to_df(bs.query_stock_basic(code=bs_code))
    return df.iloc[0].to_dict() if not df.empty else {}

# 用法
print(baostock_stock_basic("600519"))
# 实测：{'code': 'sh.600519', 'code_name': '贵州茅台', 'ipoDate': '2001-08-27',
#        'outDate': '', 'type': '1', 'status': '1'}   ← outDate 为空 = 仍在市
```

> 🔴 **已退市标的的除权除息，三个源全缺**（2026-08 交叉验证）：通达信 `xdxr()` 即使传对
> `market=2` 也返回 0 条、东财历史快照同样没有、baostock 直接拒绝北交所代码。
> 已退市标的（尤其北交所）**做复权必然对不上**，不是本工具包的缺陷，是源侧的保留策略。

---

### 6.7 申万行业分类历史 — 消除行业前视偏差（V3.7.0 新增）

**核心价值：** §3.7 `industry_comparison()` 用东财，**只有当前归属**。做历史研究时用今天的
行业分类去套过去，是典型的**前视偏差**。本端点给出每只股票的**行业变迁史**。

⚠️ 申万官方只发布**代码**不发布中文名（名称表是另一份未公开发布）。
东财/通达信的行业名**不能**直接套——分类体系不同，代码不通用。

```python
import io

from typing import Optional

import pandas as pd
import requests

SW_URL = "https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls"

def sw_industry_history() -> pd.DataFrame:
    """申万行业归属变迁史 — 每只股票每次行业调整一行"""
    try:
        r = requests.get(SW_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
    except requests.exceptions.SSLError as e:
        # 2026-08-19 实测：纯 certifi 环境握手正常，证书链完整，无需手动补中间证书。
        # 保留此分支是为了在站点证书回归时给出可操作的提示，而不是吞掉异常。
        raise RuntimeError(
            "申万站点 SSL 握手失败。2026-08 实测其证书链正常，若你遇到此错误，"
            "多半是本机 CA 包过旧或中间人代理：先试 `pip install -U certifi`。"
            f"原始错误: {e}"
        ) from e
    df = pd.read_excel(io.BytesIO(r.content))
    df = df.rename(columns={"股票代码": "code", "计入日期": "start_date",
                            "行业代码": "industry_code", "更新日期": "update_date"})
    missing = {"code", "start_date", "industry_code"} - set(df.columns)
    if missing:
        raise RuntimeError(f"申万表结构变了，缺列 {sorted(missing)}；实际列={list(df.columns)}")
    df["code"] = df["code"].astype(str).str.zfill(6)
    df["industry_code"] = df["industry_code"].astype(str).str.zfill(6)
    # 层级码要补成规范的 6 位（申万官方一级是 480000、二级是 480300），
    # 直接截断成 "48"/"4803" 无法与官方指数/名称表 join。
    df["l1_code"] = df["industry_code"].str[:2] + "0000"    # 一级，如 480000
    df["l2_code"] = df["industry_code"].str[:4] + "00"      # 二级，如 480300
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    return df.sort_values(["code", "start_date"]).reset_index(drop=True)

def sw_industry_as_of(df: pd.DataFrame, code: str, as_of: str) -> Optional[dict]:
    """某只股票在 as_of 日所属的申万行业（取不晚于该日的最后一次调整）"""
    code = str(code).zfill(6)
    sub = df[(df["code"] == code) & (df["start_date"] <= pd.Timestamp(as_of))]
    if sub.empty:
        return None                  # 该日尚未上市 / 无归属记录
    row = sub.iloc[-1]
    return {"code": code, "as_of": as_of,
            "industry_code": row["industry_code"],
            "l1_code": row["l1_code"], "l2_code": row["l2_code"],
            "since": row["start_date"].strftime("%Y-%m-%d")}

# 用法
sw = sw_industry_history()
print(len(sw), "行 |", sw["code"].nunique(), "只标的 |",
      sw["l1_code"].nunique(), "个一级行业")
# 实测 2026-08-19：12893 行 | 5905 只 | 38 个一级 / 194 个二级 / 553 个三级

# 前视偏差验证：平安银行在不同时点属于不同行业
for d in ("2013-01-01", "2016-01-01", "2026-08-18"):
    print(d, sw_industry_as_of(sw, "000001", d))
# 2013-01-01 → 440101（一级 440000，自 1991-04-03）
# 2016-01-01 → 480101（一级 480000，自 2014-02-21）
# 2026-08-18 → 480301（一级 480000 / 二级 480300，自 2021-07-30）
```

> **典型用法：** 做行业轮动回测时，每个调仓日调用 `sw_industry_as_of()` 取**当时**的归属，
> 而不是用一张当前分类表贯穿全程。实测有标的历史上变更过 **10 次**行业。

---



## 估值计算公式

### 前向PE

```python
def forward_pe(price: float, eps_forecast: float) -> float:
    """前向PE = 当前股价 / 未来年度一致预期EPS"""
    if eps_forecast <= 0:
        return float("inf")
    return price / eps_forecast
```

### PE消化时间

```python
import math

def pe_digestion(current_pe: float, cagr: float, target_pe: float = 30) -> float:
    """
    当前PE消化到目标PE需要多少年。
    target_pe 固定30x（A股成长股合理估值锚点）。
    cagr: 用 下一年EPS / 当年EPS - 1
    """
    if current_pe <= target_pe:
        return 0.0
    if cagr <= 0:
        return float("inf")
    return math.log(current_pe / target_pe) / math.log(1 + cagr)
```

### PEG

```python
def calc_peg(pe: float, cagr: float) -> float:
    """
    PEG = 前向PE / (CAGR * 100)
    PEG < 1   → 便宜
    PEG 1-1.5 → 合理
    PEG > 1.5 → 贵
    """
    if cagr <= 0:
        return float("inf")
    return pe / (cagr * 100)
```

### 投资框架速查

```
壁垒 → 增速 → PE消化 → PEG校验

1. 有壁垒吗？(tech_moat / capacity_moat) → 没有则排除
2. 增速多少？(CAGR > 30% 才有意义)
3. PE多久消化到30x？(< 2年合理, > 4年太贵)
4. PEG多少？(< 1 便宜, 1-1.5 合理, > 1.5 贵)

30x PE 锚点: A股成长股的合理估值重力线，所有行业统一用30x。
期权定价例外: PEG > 3 但壁垒极深时，本质是看涨期权，不适用PEG框架。
```

---


