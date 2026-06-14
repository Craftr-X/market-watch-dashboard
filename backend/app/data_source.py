from __future__ import annotations

from datetime import date


def load_market_data(trading_day: date | None = None) -> dict:
    day = (trading_day or date.today()).isoformat()
    return {
        "date": day,
        "source": "sample-akshare-compatible",
        "indices": [
            {"index_code": "000001", "index_name": "上证指数", "close": 3048.22, "change_pct": 0.84, "turnover": 3890_000_000_000},
            {"index_code": "399001", "index_name": "深证成指", "close": 9521.68, "change_pct": 1.21, "turnover": 5120_000_000_000},
            {"index_code": "399006", "index_name": "创业板指", "close": 1876.31, "change_pct": 1.66, "turnover": 2210_000_000_000},
            {"index_code": "000300", "index_name": "沪深300", "close": 3568.44, "change_pct": 0.92, "turnover": 2430_000_000_000},
            {"index_code": "000510", "index_name": "中证A500", "close": 4521.73, "change_pct": 1.04, "turnover": 2860_000_000_000},
            {"index_code": "000905", "index_name": "中证500", "close": 5488.25, "change_pct": 1.37, "turnover": 1980_000_000_000},
        ],
        "sectors": [
            {"sector_name": "机器人", "sector_type": "concept", "change_pct": 4.82, "turnover": 132_000_000_000, "leading_stocks": "埃斯顿, 机器人, 汇川技术"},
            {"sector_name": "半导体", "sector_type": "industry", "change_pct": 3.76, "turnover": 188_000_000_000, "leading_stocks": "中芯国际, 北方华创, 韦尔股份"},
            {"sector_name": "券商", "sector_type": "industry", "change_pct": 2.64, "turnover": 96_000_000_000, "leading_stocks": "东方财富, 中信证券, 华泰证券"},
            {"sector_name": "银行", "sector_type": "industry", "change_pct": 0.72, "turnover": 82_000_000_000, "leading_stocks": "平安银行, 招商银行"},
            {"sector_name": "地产", "sector_type": "industry", "change_pct": -0.88, "turnover": 54_000_000_000, "leading_stocks": "万科A, 保利发展"},
        ],
        "stocks": [
            {"code": "002747", "name": "埃斯顿", "close": 18.43, "change_pct": 7.8, "turnover": 2_150_000_000, "volume_ratio": 2.8, "market_cap": 16_100_000_000, "industry": "机器人", "concept": "机器人", "is_st": False, "is_suspended": False, "five_day_change_pct": 16.4, "trend_breakout": True},
            {"code": "300024", "name": "机器人", "close": 14.62, "change_pct": 6.9, "turnover": 1_860_000_000, "volume_ratio": 2.5, "market_cap": 22_600_000_000, "industry": "机器人", "concept": "机器人", "is_st": False, "is_suspended": False, "five_day_change_pct": 14.2, "trend_breakout": True},
            {"code": "002371", "name": "北方华创", "close": 298.2, "change_pct": 5.6, "turnover": 4_900_000_000, "volume_ratio": 2.0, "market_cap": 158_000_000_000, "industry": "半导体", "concept": "芯片", "is_st": False, "is_suspended": False, "five_day_change_pct": 10.7, "trend_breakout": True},
            {"code": "300059", "name": "东方财富", "close": 15.08, "change_pct": 4.1, "turnover": 5_500_000_000, "volume_ratio": 1.8, "market_cap": 238_000_000_000, "industry": "券商", "concept": "互联网金融", "is_st": False, "is_suspended": False, "five_day_change_pct": 7.8, "trend_breakout": False},
            {"code": "000001", "name": "平安银行", "close": 11.28, "change_pct": 1.1, "turnover": 1_250_000_000, "volume_ratio": 1.2, "market_cap": 219_000_000_000, "industry": "银行", "concept": "大金融", "is_st": False, "is_suspended": False, "five_day_change_pct": 2.2, "trend_breakout": False},
            {"code": "000002", "name": "万科A", "close": 7.16, "change_pct": -1.9, "turnover": 780_000_000, "volume_ratio": 1.6, "market_cap": 85_000_000_000, "industry": "地产", "concept": "地产", "is_st": False, "is_suspended": False, "five_day_change_pct": -4.3, "trend_breakout": False},
            {"code": "000003", "name": "ST观察", "close": 2.48, "change_pct": 4.9, "turnover": 33_000_000, "volume_ratio": 2.6, "market_cap": 1_200_000_000, "industry": "地产", "concept": "低价股", "is_st": True, "is_suspended": False, "five_day_change_pct": 28.1, "trend_breakout": True},
        ],
    }
