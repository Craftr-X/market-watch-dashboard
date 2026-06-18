#!/usr/bin/env python
"""v0.3.0 全链路验收脚本 — 覆盖后端 API、数据库表结构、Python 模块、前端页面"""
import json
import sqlite3
import time
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote

BASE = "http://127.0.0.1:8000"
FRONTEND = "http://localhost:3000"
from app.config import DEFAULT_DB_PATH
DB_PATH = DEFAULT_DB_PATH
PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results = []


def report(name, status, detail=""):
    results.append((name, status, detail))
    print(f"[{status}] {name} {('- ' + detail) if detail else ''}")


def http_get(path, timeout=120):
    url = BASE + path
    start = time.time()
    try:
        with urlopen(url, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            ms = int((time.time() - start) * 1000)
            return r.status, json.loads(raw), ms
    except Exception as e:
        # 4xx/5xx 也可能有响应体
        resp = getattr(e, "read", None)
        status = getattr(e, "code", 0)
        body = {}
        if resp is not None:
            try:
                raw = resp().decode("utf-8")
                body = json.loads(raw)
            except Exception:
                pass
        return status, body if body else {"error": str(e)}, int((time.time() - start) * 1000)


# ============================================================================
# Phase 1: 后端健康
# ============================================================================
print("\n=== 1. 后端健康检查 ===")
code, d, ms = http_get("/api/scheduler/status", timeout=10)
if code == 200 and "running" in d:
    report("服务启动正常", PASS, f"{ms}ms, running={d['running']}")
else:
    report("服务启动正常", FAIL, f"HTTP {code}")

# ============================================================================
# Phase 2: 核心 API (既有功能)
# ============================================================================
print("\n=== 2. 核心市场 API ===")
for name, path in [
    ("市场概览", "/api/market/overview"),
    ("板块排名", "/api/sectors/rank"),
    ("强势股", "/api/stocks/strong"),
    ("风险股", "/api/stocks/risk"),
    ("每日复盘", "/api/reports/daily"),
]:
    code, d, ms = http_get(path, timeout=30)
    if code == 200 and "data" in d:
        report(name, PASS, f"{ms}ms")
    else:
        report(name, FAIL, f"HTTP {code}")

# ============================================================================
# Phase 3: 新增 API — 股票搜索
# ============================================================================
print("\n=== 3. 股票搜索 API ===")

# 代码搜索
code, d, ms = http_get("/api/stocks/search?q=600", timeout=30)
if code == 200 and "data" in d:
    items = d["data"].get("items", []) if isinstance(d["data"], dict) else []
    n = len(items)
    report("按代码前缀搜索(600)", PASS if n > 0 else WARN, f"命中 {n} 条, {ms}ms")
else:
    report("按代码前缀搜索(600)", FAIL, f"HTTP {code}")

# 中文搜索（需 URL 编码）
code, d, ms = http_get(f"/api/stocks/search?q={quote('茅台')}", timeout=30)
if code == 200 and "data" in d:
    items = d["data"].get("items", []) if isinstance(d["data"], dict) else []
    n = len(items)
    report("按名称模糊搜索(茅台)", PASS if n > 0 else WARN, f"命中 {n} 条, {ms}ms")
else:
    report("按名称模糊搜索(茅台)", FAIL, f"HTTP {code}")

# 精确代码搜索
code, d, ms = http_get("/api/stocks/search?q=600519", timeout=30)
if code == 200 and "data" in d:
    items = d["data"].get("items", []) if isinstance(d["data"], dict) else []
    report("精确代码搜索(600519)", PASS if len(items) >= 1 else FAIL, f"命中 {len(items)} 条")
else:
    report("精确代码搜索(600519)", FAIL, f"HTTP {code}")

# ============================================================================
# Phase 4: 新增 API — 个股历史行情
# ============================================================================
print("\n=== 4. 个股历史行情 API ===")

test_cases = [
    ("贵州茅台 日线", "600519", "daily", "qfq"),
    ("平安银行 日线", "000001", "daily", "qfq"),
    ("平安银行 周线", "000001", "weekly", "qfq"),
    ("宁德时代 月线", "300750", "monthly", "qfq"),
    ("不复权切换", "600519", "daily", "none"),
]

for case_name, code_val, period, adjust in test_cases:
    url = f"/api/stocks/history?code={code_val}&period={period}&adjust={adjust}"
    status, d, ms = http_get(url, timeout=120)
    if status == 200 and "data" in d:
        data = d["data"]
        candles = data.get("candles", []) if isinstance(data, dict) else []
        source = data.get("source", "unknown") if isinstance(data, dict) else "unknown"
        report(
            case_name,
            PASS if len(candles) > 0 else WARN,
            f"{len(candles)} 根, source={source}, {ms}ms"
        )
    else:
        report(case_name, FAIL, f"HTTP {status}, {str(d)[:100]}")

# 边界条件
code, d, ms = http_get("/api/stocks/history?code=abc&period=daily", timeout=10)
report("非法代码(abc)", PASS if code == 400 else FAIL, f"HTTP {code}")

code, d, ms = http_get("/api/stocks/history?code=999999&period=daily", timeout=120)
# 未上市股票：在降级策略下，999999 不是种子股票，应返回错误
report("未上市股票(999999)", WARN if code == 200 else PASS, f"HTTP {code}")

# ============================================================================
# Phase 5: 数据库表结构
# ============================================================================
print("\n=== 5. 数据库表结构 ===")

if DB_PATH.exists():
    report(f"数据库存在 ({DB_PATH})", PASS)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    required_tables = ["market_snapshot", "stock_daily", "sector_daily",
                       "daily_report", "stock_history", "stock_info"]
    for tbl in required_tables:
        exists = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
        ).fetchone()
        count = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0] if exists else 0
        report(f"表 {tbl} (有 {count} 条)", PASS if exists else FAIL)

    # stock_info 应该至少有种子股票
    si_count = cur.execute("SELECT COUNT(*) FROM stock_info").fetchone()[0]
    report(f"stock_info 有数据 (>=1 条)", PASS if si_count >= 1 else FAIL, f"{si_count} 条")

    conn.close()
else:
    report(f"数据库存在 ({DB_PATH})", FAIL, "路径不存在")

# ============================================================================
# Phase 6: Python 模块
# ============================================================================
print("\n=== 6. Python 模块 ===")

for mod in ["app.history", "app.search", "app.storage", "app.main"]:
    try:
        __import__(mod)
        report(f"模块 {mod} 可导入", PASS)
    except Exception as e:
        report(f"模块 {mod} 可导入", FAIL, str(e))

# 关键函数行为
try:
    from app.history import _validate_code
    assert _validate_code("600519") == "600519"
    report("_validate_code", PASS)
except Exception as e:
    report("_validate_code", FAIL, str(e))

try:
    from app.history import _date_range
    s, e = _date_range("daily")
    assert isinstance(s, str) and "-" in s
    report("_date_range daily", PASS, f"{s} -> {e}")
except Exception as e:
    report("_date_range daily", FAIL, str(e))

try:
    from app.history import fetch_history
    result = fetch_history("600519", "daily", "qfq")
    report("fetch_history(600519) 直接调用",
           PASS if result and result.candles else FAIL,
           f"{len(result.candles)} candles, source={result.source}")
except Exception as e:
    report("fetch_history(600519) 直接调用", FAIL, str(e))

# ============================================================================
# Phase 7: 前端页面可达性
# ============================================================================
print("\n=== 7. 前端页面 ===")

for name, url_path in [
    ("首页", "/"),
    ("个股详情 600519", "/stock/600519"),
    ("个股详情 000001", "/stock/000001"),
    ("个股详情 300750", "/stock/300750"),
]:
    try:
        with urlopen(FRONTEND + url_path, timeout=15) as r:
            html = r.read(200).decode("utf-8", errors="ignore")
            report(f"{name} HTTP 200", PASS, f"返回 {len(html)}+ 字符")
    except Exception as e:
        report(f"{name} HTTP 200", FAIL, str(e))

# ============================================================================
# Phase 8: 汇总
# ============================================================================
print("\n" + "=" * 60)
print("📋 验收结果汇总")
print("=" * 60)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
warned = sum(1 for _, s, _ in results if s == WARN)
total = len(results)
print(f"共 {total} 项  |  ✅ {passed}  |  ⚠️ {warned}  |  ❌ {failed}")

if failed > 0:
    print("\n❌ 失败项明细:")
    for name, s, d in results:
        if s == FAIL:
            print(f"   ❌ {name} — {d}")
if warned > 0:
    print("\n⚠️ 警告项明细:")
    for name, s, d in results:
        if s == WARN:
            print(f"   ⚠️ {name} — {d}")

print(f"\n时间: {datetime.now().isoformat(timespec='seconds')}")

if failed > 0:
    sys.exit(1)
sys.exit(0)
