from __future__ import annotations


def market_temperature(indices: list[dict]) -> str:
    avg_change = sum(float(item["change_pct"]) for item in indices) / max(len(indices), 1)
    if avg_change >= 1:
        return "偏强"
    if avg_change <= -0.8:
        return "偏弱"
    return "分化"


def build_daily_report(indices: list[dict], sectors: list[dict], stocks: list[dict]) -> dict:
    state = market_temperature(indices)
    strong_sectors = [item["sector_name"] for item in sorted(sectors, key=lambda x: x["change_pct"], reverse=True)[:3]]
    strong_stocks = [f'{item["name"]}({item["code"]})' for item in stocks[:5]]
    risk_notes = sorted({tag for stock in stocks for tag in stock["risk_tags"]}) or ["暂无突出风险标签，仍需控制仓位和预期"]
    summary = (
        f"今日市场：{state}。强势方向集中在{'、'.join(strong_sectors)}。"
        f"观察股票以{ '、'.join(strong_stocks) }为主，但均仅用于复盘学习。"
        "基金/宽基定投通常不因为一天行情改变长期计划。"
    )
    return {
        "summary": summary,
        "strong_sectors": strong_sectors,
        "strong_stocks": strong_stocks,
        "risk_notes": risk_notes,
    }
