from backend.app.scoring import score_strong_stocks


def test_scores_prioritize_liquidity_sector_strength_and_penalize_risk():
    stocks = [
        {
            "code": "000001",
            "name": "平安银行",
            "change_pct": 4.2,
            "turnover": 9_000_000_000,
            "volume_ratio": 2.1,
            "market_cap": 220_000_000_000,
            "industry": "银行",
            "concept": "大金融",
            "is_st": False,
            "is_suspended": False,
            "five_day_change_pct": 6.5,
            "trend_breakout": True,
        },
        {
            "code": "000002",
            "name": "小成交高涨",
            "change_pct": 9.9,
            "turnover": 12_000_000,
            "volume_ratio": 0.8,
            "market_cap": 1_500_000_000,
            "industry": "地产",
            "concept": "低价股",
            "is_st": False,
            "is_suspended": False,
            "five_day_change_pct": 38.0,
            "trend_breakout": False,
        },
        {
            "code": "000003",
            "name": "ST样本",
            "change_pct": 5.0,
            "turnover": 700_000_000,
            "volume_ratio": 1.7,
            "market_cap": 5_000_000_000,
            "industry": "银行",
            "concept": "大金融",
            "is_st": True,
            "is_suspended": False,
            "five_day_change_pct": 7.0,
            "trend_breakout": True,
        },
    ]
    sector_strength = {"银行": 3.2, "地产": -0.6}

    ranked = score_strong_stocks(stocks, sector_strength, limit=3)

    assert ranked[0]["code"] == "000001"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "成交额放大" in ranked[0]["strength_reason"]
    assert ranked[1]["risk_tags"]
    assert ranked[2]["risk_tags"] == ["ST/退市风险"]


def test_every_ranked_stock_contains_reason_and_risk_note():
    ranked = score_strong_stocks(
        [
            {
                "code": "600000",
                "name": "浦发银行",
                "change_pct": 1.2,
                "turnover": 500_000_000,
                "volume_ratio": 1.1,
                "market_cap": 100_000_000_000,
                "industry": "银行",
                "concept": "大金融",
                "is_st": False,
                "is_suspended": False,
                "five_day_change_pct": 2.5,
                "trend_breakout": False,
            }
        ],
        {"银行": 0.8},
        limit=1,
    )

    assert ranked[0]["strength_reason"]
    assert ranked[0]["risk_note"]
    assert "不代表买入建议" in ranked[0]["risk_note"]
