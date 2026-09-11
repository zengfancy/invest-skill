#!/usr/bin/env python3
"""Fetch Hengrui / 恒瑞医药 (600276) research snapshot. Writes JSON/CSV under data/."""
from __future__ import annotations

import json
import math
import os
import random
import re
import socket
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Optional

import baostock as bs
import pandas as pd
import requests
from mootdx.quotes import Quotes

ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
REPORT_API = "https://reportapi.eastmoney.com/report/list"

# ── core helpers ──────────────────────────────────────────────────────────
_TDX_SERVERS = [
    ("119.97.185.59", 7709), ("124.70.133.119", 7709), ("116.205.183.150", 7709),
    ("123.60.73.44", 7709), ("116.205.163.254", 7709), ("121.36.225.169", 7709),
    ("123.60.70.228", 7709), ("124.71.9.153", 7709), ("110.41.147.114", 7709),
    ("124.71.187.122", 7709),
]
SH_INDEX = {"000300", "000905", "000016", "000688", "000852", "000010"}
_TICKER_RE = re.compile(
    r"^(?:(sh|sz|bj)(\d{6})|(\d{6})(?:\.(sh|sz|bj))?)$", re.IGNORECASE
)

EM_SESSION = requests.Session()
EM_SESSION.headers.update({"User-Agent": UA})
EM_MIN_INTERVAL = 1.0
_em_last_call = [0.0]


def _probe(ip, port, timeout=2.0):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def _validate(client, market: str = "std") -> bool:
    if market != "std":
        return True
    try:
        df = client.bars(symbol="000001", frequency=9, offset=1)
        return df is not None and not df.empty
    except Exception:
        return False


def tdx_client(market="std"):
    for ip, port in _TDX_SERVERS:
        if not _probe(ip, port):
            continue
        try:
            c = Quotes.factory(market=market, server=(ip, port))
            if _validate(c, market):
                return c
        except Exception:
            continue
    for kwargs in ({"bestip": True}, {}):
        try:
            c = Quotes.factory(market=market, **kwargs)
            if _validate(c, market):
                return c
        except Exception:
            continue
    raise RuntimeError("所有 mootdx 服务器均无法取到数据")


def get_prefix(code: str) -> str:
    c = code.lower().strip()
    if c.endswith((".sh", ".sz", ".bj")):
        return c[-2:]
    if c.startswith(("sh", "sz", "bj")):
        return c[:2]
    if c.startswith("92"):
        return "bj"
    if c.startswith(("5", "6", "9")):
        return "sh"
    if c.startswith(("4", "8")):
        return "bj"
    if c in SH_INDEX:
        return "sh"
    return "sz"


def _natural_market(digits: str) -> str:
    if digits.startswith(("4", "8", "92")):
        return "bj"
    if digits[0] in ("5", "6", "9"):
        return "sh"
    return "sz"


def norm_ticker(code: str, stock_only: bool = False) -> str:
    raw = str(code).strip()
    m = _TICKER_RE.match(raw)
    if not m:
        raise ValueError(f"无法把 {code!r} 解析为 6 位股票代码")
    digits = m.group(2) or m.group(3)
    market = (m.group(1) or m.group(4) or "").lower()
    if market:
        if digits.startswith("000"):
            if market == "bj":
                raise ValueError(f"{code!r} 市场标识与号段矛盾")
            if stock_only and market == "sh":
                raise ValueError(f"{code!r} 指向沪市指数而非个股")
        else:
            nat = _natural_market(digits)
            if market != nat:
                raise ValueError(f"{code!r} 的市场标识与号段矛盾")
    return digits


def em_market_code(code: str) -> int:
    return 1 if get_prefix(code) == "sh" else 0


def em_get(url: str, params: Optional[dict] = None, headers: Optional[dict] = None,
           timeout: int = 15, **kwargs):
    wait = EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
    if wait > 0:
        time.sleep(wait + random.uniform(0.1, 0.5))
    try:
        return EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    finally:
        _em_last_call[0] = time.time()


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(x) for x in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if pd.isna(obj) if not isinstance(obj, (list, dict)) else False:
        return None
    if isinstance(obj, (float,)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    if hasattr(obj, "item"):
        try:
            return json_safe(obj.item())
        except Exception:
            return str(obj)
    return obj


def save_json(name, obj):
    path = os.path.join(ROOT, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(json_safe(obj), f, ensure_ascii=False, indent=2)
    print(f"wrote {name}")
    return path


def tencent_quote(codes: list[str]) -> dict:
    import urllib.request
    prefixed = []
    key_of = {}
    for c in codes:
        low = c.lower()
        if low.startswith(("sh", "sz", "bj")):
            p = low
        elif c.startswith("92"):
            p = f"bj{c}"
        elif c in SH_INDEX or c.startswith(("5", "6", "9")):
            p = f"sh{c}"
        elif c.startswith(("4", "8")):
            p = f"bj{c}"
        else:
            p = f"sz{c}"
        prefixed.append(p)
        key_of[p] = c
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
        code = key_of.get(key, key[2:])
        result[code] = {
            "name": vals[1],
            "price": float(vals[3]) if vals[3] else 0,
            "last_close": float(vals[4]) if vals[4] else 0,
            "open": float(vals[5]) if vals[5] else 0,
            "change_amt": float(vals[31]) if vals[31] else 0,
            "change_pct": float(vals[32]) if vals[32] else 0,
            "high": float(vals[33]) if vals[33] else 0,
            "low": float(vals[34]) if vals[34] else 0,
            "amount_wan": float(vals[37]) if vals[37] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "pe_ttm": float(vals[39]) if vals[39] else 0,
            "amplitude_pct": float(vals[43]) if vals[43] else 0,
            "float_mcap_yi": float(vals[44]) if vals[44] else 0,
            "mcap_yi": float(vals[45]) if vals[45] else 0,
            "pb": float(vals[46]) if vals[46] else 0,
            "limit_up": float(vals[47]) if vals[47] else 0,
            "limit_down": float(vals[48]) if vals[48] else 0,
            "vol_ratio": float(vals[49]) if vals[49] else 0,
            "pe_static": float(vals[52]) if vals[52] else 0,
        }
        q = result[code]
        q["is_stale"] = (q["amount_wan"] == 0 and q["price"] == q["last_close"] and q["price"] > 0)
    return result


def sina_financial_report(code: str, report_type: str = "lrb", num: int = 12) -> list:
    prefix = get_prefix(code)
    paper_code = f"{prefix}{code}"
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"
    params = {
        "paperCode": paper_code, "source": report_type, "type": "0",
        "page": "1", "num": str(num),
    }
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
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


@contextmanager
def bs_session():
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock 登录失败: {lg.error_code} {lg.error_msg}")
    try:
        yield
    finally:
        bs.logout()


def _rs_to_df(rs) -> pd.DataFrame:
    if rs.error_code != "0":
        raise RuntimeError(f"baostock 查询失败: {rs.error_code} {rs.error_msg}")
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    return pd.DataFrame(rows, columns=rs.fields)


def _bs_code(code: str) -> str:
    code = str(code).zfill(6)
    if code[:2] in ("60", "68", "90"):
        return f"sh.{code}"
    if code[:2] in ("00", "30", "20"):
        return f"sz.{code}"
    raise ValueError(f"baostock 不支持该代码: {code}")


def baostock_valuation_history(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    bs_code = _bs_code(code)
    fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM,turn,tradestatus,isST"
    with bs_session():
        rs = bs.query_history_k_data_plus(
            bs_code, fields, start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="3",
        )
        df = _rs_to_df(rs)
    for c in ("close", "peTTM", "pbMRQ", "psTTM", "pcfNcfTTM", "turn"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def eastmoney_stock_info(code: str) -> dict:
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "fltt": "2", "invt": "2",
        "fields": "f57,f58,f84,f85,f127,f116,f117,f189,f43",
        "secid": f"{em_market_code(code)}.{code}",
    }
    r = em_get(url, params=params, headers={"User-Agent": UA}, timeout=10)
    d = r.json().get("data", {}) or {}
    return {
        "code": d.get("f57", ""),
        "name": d.get("f58", ""),
        "industry": d.get("f127", ""),
        "total_shares": d.get("f84", 0),
        "float_shares": d.get("f85", 0),
        "mcap": d.get("f116", 0),
        "float_mcap": d.get("f117", 0),
        "list_date": str(d.get("f189", "")),
        "price": d.get("f43", 0),
    }


def eastmoney_reports(code: str, max_pages: int = 3) -> list:
    code = norm_ticker(code, stock_only=True)
    all_records = []
    for page in range(1, max_pages + 1):
        params = {
            "industryCode": "*", "pageSize": "100", "industry": "*",
            "rating": "*", "ratingChange": "*",
            "beginTime": "2024-01-01", "endTime": "2030-01-01",
            "pageNo": str(page), "fields": "", "qType": "0",
            "orgCode": "", "code": code, "rcode": "",
            "p": str(page), "pageNum": str(page), "pageNumber": str(page),
        }
        r = em_get(REPORT_API, params=params,
                   headers={"Referer": "https://data.eastmoney.com/"}, timeout=30)
        d = r.json()
        rows = d.get("data") or []
        if not rows:
            break
        slim = []
        for rec in rows:
            slim.append({
                "title": rec.get("title"),
                "publishDate": (rec.get("publishDate") or "")[:10],
                "orgSName": rec.get("orgSName"),
                "emRatingName": rec.get("emRatingName"),
                "predictThisYearEps": rec.get("predictThisYearEps"),
                "predictNextYearEps": rec.get("predictNextYearEps"),
                "predictNextTwoYearEps": rec.get("predictNextTwoYearEps"),
                "indvInduName": rec.get("indvInduName"),
            })
        all_records.extend(slim)
        if page >= (d.get("TotalPage", 1) or 1):
            break
    return all_records


def ths_eps_forecast(code: str):
    code = norm_ticker(code, stock_only=True)
    url = f"https://basic.10jqka.com.cn/new/{code}/worth.html"
    headers = {
        "User-Agent": UA,
        "Referer": "https://basic.10jqka.com.cn/",
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.encoding = "gbk"
    dfs = pd.read_html(StringIO(r.text))
    for df in dfs:
        cols = [str(c) for c in df.columns]
        if any("每股收益" in c or "均值" in c for c in cols):
            return df
    return dfs[0] if dfs else pd.DataFrame()


def eastmoney_stock_news(code: str, page_size: int = 40) -> list:
    cb = "jQuery_news"
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    inner_params = json.dumps({
        "uid": "", "keyword": code, "type": ["cmsArticleWebOld"],
        "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {
            "searchScope": "default", "sort": "default",
            "pageIndex": 1, "pageSize": page_size, "preTag": "", "postTag": "",
        }},
    }, separators=(",", ":"))
    params = {"cb": cb, "param": inner_params}
    r = em_get(url, params=params, headers={"User-Agent": UA, "Referer": "https://so.eastmoney.com/"}, timeout=15)
    text = r.text
    if "(" not in text:
        return []
    json_str = text[text.index("(") + 1: text.rindex(")")]
    d = json.loads(json_str)
    rows = []
    articles = d.get("result", {}).get("cmsArticleWebOld", []) or []
    for a in articles:
        rows.append({
            "title": re.sub(r"<[^>]+>", "", a.get("title", "")),
            "content": re.sub(r"<[^>]+>", "", a.get("content", ""))[:300],
            "time": a.get("date", ""),
            "source": a.get("mediaName", ""),
            "url": a.get("url", ""),
        })
    return rows


_CNINFO_ORGID_MAP = {}


def _cninfo_ts_to_date(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
    return str(ts)[:10] if ts else ""


def _cninfo_orgid(code: str) -> str:
    global _CNINFO_ORGID_MAP
    if not _CNINFO_ORGID_MAP:
        try:
            r = requests.get("http://www.cninfo.com.cn/new/data/szse_stock.json",
                             headers={"User-Agent": UA}, timeout=15)
            _CNINFO_ORGID_MAP = {s["code"]: s["orgId"]
                                 for s in r.json().get("stockList", [])}
        except Exception as e:
            print(f"[WARN] 巨潮 orgId 映射表拉取失败: {e}")
    org = _CNINFO_ORGID_MAP.get(code)
    if org:
        return org
    return f"gs{get_prefix(code)}0{code}"


def cninfo_announcements(code: str, page_size: int = 40) -> list:
    url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    org_id = _cninfo_orgid(code)
    payload = {
        "stock": f"{code},{org_id}", "tabName": "fulltext",
        "pageSize": str(page_size), "pageNum": "1",
        "column": "", "category": "", "plate": "", "seDate": "",
        "searchkey": "", "secid": "", "sortName": "", "sortType": "",
        "isHLtitle": "true",
    }
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.cninfo.com.cn/new/disclosure",
        "Origin": "https://www.cninfo.com.cn",
    }
    r = requests.post(url, data=payload, headers=headers, timeout=15)
    d = r.json()
    rows = []
    for item in d.get("announcements", []) or []:
        rows.append({
            "title": item.get("announcementTitle", ""),
            "type": item.get("announcementTypeName", ""),
            "date": _cninfo_ts_to_date(item.get("announcementTime")),
            "url": f"https://www.cninfo.com.cn/new/disclosure/detail?annoId={item.get('announcementId', '')}",
        })
    return rows


def df_to_records(df: pd.DataFrame, n=None):
    if df is None or df.empty:
        return []
    if n:
        df = df.head(n)
    recs = json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))
    return recs


def valuation_percentiles(df: pd.DataFrame, years=5):
    if df is None or df.empty:
        return {}
    d = df.copy()
    d = d[d["tradestatus"].astype(str) == "1"]
    cutoff = (pd.Timestamp(d["date"].max()) - pd.DateOffset(years=years)).strftime("%Y-%m-%d")
    d = d[d["date"] >= cutoff]
    out = {}
    last = d.iloc[-1]
    for col, name in [("peTTM", "pe"), ("pbMRQ", "pb"), ("psTTM", "ps")]:
        s = d[col].dropna()
        s = s[s > 0]
        if s.empty:
            continue
        cur = float(last[col]) if pd.notna(last[col]) else None
        out[name] = {
            "current": cur,
            "min": float(s.min()),
            "max": float(s.max()),
            "median": float(s.median()),
            "p25": float(s.quantile(0.25)),
            "p75": float(s.quantile(0.75)),
            "percentile": float((s <= cur).mean() * 100) if cur is not None else None,
            "n": int(len(s)),
            "start": str(d["date"].min()),
            "end": str(d["date"].max()),
        }
    return out


def pick_num(rec, keys):
    for k in keys:
        if k in rec and rec[k] not in (None, "", "-"):
            try:
                return float(str(rec[k]).replace(",", "").replace("%", ""))
            except Exception:
                continue
    return None


def main():
    log = {"started": datetime.now().isoformat(), "today": TODAY, "errors": []}
    TARGET = "600276"
    PEERS = ["600276", "600196", "002422", "000661", "002821"]  # 恒瑞、复星医药、科伦药业、长春高新、凯莱英
    INDEXES = ["sz399006", "sh000300", "sz399303"]  # 创业板 / 沪深300; 医药指数可后续替换

    # 1) quotes
    try:
        quotes = tencent_quote(PEERS + ["sz399006", "sh000300"])
        save_json("quotes.json", quotes)
        log["quotes"] = {k: quotes[k].get("name") for k in quotes}
    except Exception as e:
        log["errors"].append(f"quotes: {e}")
        quotes = {}

    # 2) eastmoney info
    try:
        info = eastmoney_stock_info(TARGET)
        save_json("stock_info.json", info)
        log["industry"] = info.get("industry")
    except Exception as e:
        log["errors"].append(f"stock_info: {e}")
        info = {}

    # 3) sina 3 statements — CATL + peers income
    sina = {}
    for code in PEERS:
        try:
            sina[code] = {
                "lrb": sina_financial_report(code, "lrb", 12),
                "fzb": sina_financial_report(code, "fzb", 12) if code == TARGET else sina_financial_report(code, "fzb", 6),
                "llb": sina_financial_report(code, "llb", 12) if code == TARGET else sina_financial_report(code, "llb", 6),
            }
            print(f"sina {code} lrb={len(sina[code]['lrb'])}")
        except Exception as e:
            log["errors"].append(f"sina {code}: {e}")
    save_json("sina_financials.json", sina)

    # 4) baostock valuation history
    try:
        val = baostock_valuation_history(TARGET, "2018-01-01", TODAY)
        val.to_csv(os.path.join(ROOT, "valuation_history.csv"), index=False)
        pct = {
            "y5": valuation_percentiles(val, 5),
            "y3": valuation_percentiles(val, 3),
        }
        save_json("valuation_percentiles.json", pct)
        # last 400 rows for price path
        tail = val.tail(400)
        save_json("price_path_400d.json", df_to_records(tail))
        log["val_rows"] = int(len(val))
        log["val_last"] = str(val.iloc[-1]["date"]) if len(val) else None
    except Exception as e:
        log["errors"].append(f"baostock: {e}")
        val = None

    # peer valuation last
    peer_val = {}
    for code in PEERS:
        if code == TARGET:
            continue
        try:
            dfp = baostock_valuation_history(code, "2021-01-01", TODAY)
            last = dfp.iloc[-1].to_dict() if len(dfp) else {}
            peer_val[code] = {
                "last": json_safe(last),
                "pct5": valuation_percentiles(dfp, 5),
            }
        except Exception as e:
            log["errors"].append(f"peer_val {code}: {e}")
    save_json("peer_valuation.json", peer_val)

    # 5) tdx finance + F10 + daily bars
    tdx = {}
    try:
        client = tdx_client()
        fin = client.finance(symbol=TARGET)
        tdx["finance"] = json.loads(fin.to_json(orient="records", force_ascii=False)) if hasattr(fin, "to_json") else str(fin)
        f10 = {}
        for cat in ["最新提示", "公司概况", "财务分析", "资本运作", "业内点评", "行业分析", "公司大事"]:
            try:
                text = client.F10(symbol=TARGET, name=cat)
                f10[cat] = (text or "")[:8000]
            except Exception as e:
                f10[cat] = f"ERR {e}"
        tdx["f10"] = f10
        bars = client.bars(symbol=TARGET, frequency=9, offset=280)
        tdx["bars_daily"] = json.loads(bars.to_json(orient="records", force_ascii=False, date_format="iso")) if bars is not None else []
        save_json("tdx_snapshot.json", tdx)
    except Exception as e:
        log["errors"].append(f"tdx: {e}")

    # 6) reports + consensus
    try:
        reps = eastmoney_reports(TARGET, max_pages=3)
        save_json("reports.json", reps)
        log["n_reports"] = len(reps)
    except Exception as e:
        log["errors"].append(f"reports: {e}")
        reps = []

    try:
        eps = ths_eps_forecast(TARGET)
        save_json("ths_eps.json", {"columns": [str(c) for c in eps.columns], "rows": df_to_records(eps)})
        log["ths_eps_shape"] = list(eps.shape)
    except Exception as e:
        log["errors"].append(f"ths_eps: {e}")

    # 7) news + announcements
    try:
        news = eastmoney_stock_news(TARGET, 50)
        save_json("news.json", news)
        log["n_news"] = len(news)
    except Exception as e:
        log["errors"].append(f"news: {e}")
        news = []

    try:
        anns = cninfo_announcements(TARGET, 50)
        save_json("announcements.json", anns)
        log["n_anns"] = len(anns)
    except Exception as e:
        log["errors"].append(f"anns: {e}")

    # 8) derived financial KPIs from sina
    try:
        lrb = sina.get(TARGET, {}).get("lrb", [])
        fzb = sina.get(TARGET, {}).get("fzb", [])
        llb = sina.get(TARGET, {}).get("llb", [])
        derived = []
        fzb_map = {r["报告期"]: r for r in fzb}
        llb_map = {r["报告期"]: r for r in llb}
        for r in lrb:
            p = r.get("报告期")
            b = fzb_map.get(p, {})
            c = llb_map.get(p, {})
            revenue = pick_num(r, ["营业总收入", "营业收入"])
            np_attr = pick_num(r, ["归属于母公司所有者的净利润", "归属于母公司股东的净利润", "净利润"])
            np_all = pick_num(r, ["净利润"])
            gp = pick_num(r, ["营业利润"])  # not gross
            # 毛利 related
            op_cost = pick_num(r, ["营业成本", "营业总成本"])
            # try 毛利率 fields
            gm = pick_num(r, ["销售毛利率"])
            nm = pick_num(r, ["销售净利率", "净利率"])
            equity = pick_num(b, ["归属于母公司股东权益合计", "归属于母公司所有者权益合计", "所有者权益合计"])
            assets = pick_num(b, ["资产总计", "资产合计"])
            liab = pick_num(b, ["负债合计", "负债总计"])
            cash = pick_num(b, ["货币资金"])
            inv = pick_num(b, ["存货"])
            rec = pick_num(b, ["应收账款"])
            pay = pick_num(b, ["应付账款"])
            contract_liab = pick_num(b, ["合同负债"])
            st_debt = pick_num(b, ["短期借款"])
            lt_debt = pick_num(b, ["长期借款"])
            bonds = pick_num(b, ["应付债券"])
            cfo = pick_num(c, ["经营活动产生的现金流量净额"])
            capex = pick_num(c, ["购建固定资产、无形资产和其他长期资产支付的现金"])
            derived.append({
                "period": p,
                "revenue": revenue,
                "np_attr": np_attr,
                "np_all": np_all,
                "gm_field": gm,
                "nm_field": nm,
                "equity": equity,
                "assets": assets,
                "liab": liab,
                "cash": cash,
                "inventory": inv,
                "receivable": rec,
                "payable": pay,
                "contract_liab": contract_liab,
                "st_debt": st_debt,
                "lt_debt": lt_debt,
                "bonds": bonds,
                "cfo": cfo,
                "capex": capex,
                "fcf_approx": (cfo - capex) if (cfo is not None and capex is not None) else None,
                "lrb_keys": list(r.keys())[:40],
            })
        save_json("derived_kpis.json", derived)
        # dump all keys of latest lrb/fzb/llb for mapping
        save_json("sina_latest_keys.json", {
            "lrb": list(lrb[0].keys()) if lrb else [],
            "fzb": list(fzb[0].keys()) if fzb else [],
            "llb": list(llb[0].keys()) if llb else [],
            "lrb0": lrb[0] if lrb else {},
            "fzb0": {k: fzb[0][k] for k in list(fzb[0].keys())[:80]} if fzb else {},
            "llb0": llb[0] if llb else {},
        })
    except Exception as e:
        log["errors"].append(f"derived: {e}")

    log["finished"] = datetime.now().isoformat()
    save_json("fetch_log.json", log)
    print("DONE", log)


if __name__ == "__main__":
    main()
