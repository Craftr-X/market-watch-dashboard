from __future__ import annotations

from typing import Iterable


def _rank_percentiles(values: list[float]) -> dict[float, float]:
    if not values:
        return {}
    sorted_values = sorted(values)
    size = len(sorted_values)
    if size == 1:
        return {sorted_values[0]: 1.0}
    return {value: index / (size - 1) for index, value in enumerate(sorted_values)}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _risk_tags(stock: dict) -> list[str]:
    tags: list[str] = []
    if stock.get("is_st"):
        tags.append("ST/退市风险")
    if stock.get("is_suspended"):
        tags.append("停牌/异常状态")
    if float(stock.get("five_day_change_pct") or 0) >= 25:
        tags.append("近5日涨幅过高")
    if float(stock.get("turnover") or 0) < 50_000_000:
        tags.append("成交额过低")
    if float(stock.get("change_pct") or 0) < 0 and float(stock.get("volume_ratio") or 0) >= 2:
        tags.append("高位放量下跌")
    return tags


def _risk_penalty(tags: Iterable[str]) -> float:
    weights = {
        "ST/退市风险": 65,
        "停牌/异常状态": 35,
        "近5日涨幅过高": 15,
        "高位放量下跌": 20,
        "成交额过低": 18,
    }
    return sum(weights.get(tag, 8) for tag in tags)


def _reason(stock: dict, sector_strength: float, turnover_pct: float, volume_pct: float) -> str:
    reasons: list[str] = []
    if float(stock.get("change_pct") or 0) >= 3:
        reasons.append("涨幅靠前")
    if turnover_pct >= 0.65:
        reasons.append("成交额放大")
    if volume_pct >= 0.65:
        reasons.append("量比提升")
    if sector_strength > 1:
        reasons.append("所属板块同步走强")
    if stock.get("trend_breakout"):
        reasons.append("趋势突破")
    return "，".join(reasons or ["表现相对活跃"]) + "。"


def _risk_note(tags: list[str]) -> str:
    if not tags:
        return "暂无突出风险标签，但个股观察不代表买入建议，需结合长期计划独立判断。"
    return f"风险提示：{'、'.join(tags)}，个股观察不代表买入建议。"


def score_strong_stocks(
    stocks: list[dict], sector_strength: dict[str, float], limit: int = 20
) -> list[dict]:
    changes = [float(stock.get("change_pct") or 0) for stock in stocks]
    turnovers = [float(stock.get("turnover") or 0) for stock in stocks]
    volume_ratios = [float(stock.get("volume_ratio") or 0) for stock in stocks]
    change_pctile = _rank_percentiles(changes)
    turnover_pctile = _rank_percentiles(turnovers)
    volume_pctile = _rank_percentiles(volume_ratios)

    ranked: list[dict] = []
    for stock in stocks:
        change = float(stock.get("change_pct") or 0)
        turnover = float(stock.get("turnover") or 0)
        volume_ratio = float(stock.get("volume_ratio") or 0)
        sector_score = _clamp((sector_strength.get(stock.get("industry", ""), 0) + 5) / 10, 0, 1)
        trend_score = 1.0 if stock.get("trend_breakout") else 0.35
        strength = (
            change_pctile.get(change, 0) * 30
            + turnover_pctile.get(turnover, 0) * 20
            + volume_pctile.get(volume_ratio, 0) * 20
            + sector_score * 20
            + trend_score * 10
        )
        tags = _risk_tags(stock)
        score = round(_clamp(strength - _risk_penalty(tags)), 1)
        sector_value = sector_strength.get(stock.get("industry", ""), 0)
        ranked.append(
            {
                **stock,
                "score": score,
                "strength_reason": _reason(
                    stock,
                    sector_value,
                    turnover_pctile.get(turnover, 0),
                    volume_pctile.get(volume_ratio, 0),
                ),
                "risk_tags": tags,
                "risk_note": _risk_note(tags),
            }
        )

    return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]
