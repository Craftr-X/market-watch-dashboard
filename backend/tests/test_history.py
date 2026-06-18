"""
后端单元测试：history.py 核心逻辑（不依赖 AkShare）
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd


class TestValidateCode:
    """股票代码校验测试"""

    def test_accepts_valid_6digit_codes(self):
        from app.history import _validate_code
        valid_codes = ["600519", "000001", "300750", "301001", "688001"]
        for code in valid_codes:
            assert _validate_code(code) == code

    def test_strips_whitespace(self):
        from app.history import _validate_code
        assert _validate_code("  600519  ") == "600519"

    def test_rejects_short_code(self):
        from app.history import _validate_code, HistoryError, HistoryErrorCode
        with pytest.raises(HistoryError) as exc:
            _validate_code("60051")
        assert exc.value.http_status == 400
        assert exc.value.code == HistoryErrorCode.INVALID_CODE

    def test_rejects_long_code(self):
        from app.history import _validate_code, HistoryError
        with pytest.raises(HistoryError) as exc:
            _validate_code("6005199")
        assert exc.value.http_status == 400

    def test_rejects_non_digit(self):
        from app.history import _validate_code, HistoryError
        with pytest.raises(HistoryError) as exc:
            _validate_code("abcdef")
        assert exc.value.http_status == 400

    def test_rejects_empty(self):
        from app.history import _validate_code, HistoryError
        with pytest.raises(HistoryError) as exc:
            _validate_code("")
        assert exc.value.http_status == 400


class TestDateRange:
    """日期范围自动计算测试"""

    def test_daily_returns_3_years(self):
        from app.history import _date_range, _today_cn
        today = _today_cn()
        start, end = _date_range("daily")
        expected_start = (today - timedelta(days=365 * 3)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == today.isoformat()

    def test_weekly_returns_5_years(self):
        from app.history import _date_range, _today_cn
        today = _today_cn()
        start, end = _date_range("weekly")
        expected_start = (today - timedelta(days=365 * 5)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == today.isoformat()

    def test_monthly_returns_10_years(self):
        from app.history import _date_range, _today_cn
        today = _today_cn()
        start, end = _date_range("monthly")
        expected_start = (today - timedelta(days=365 * 10)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == today.isoformat()


class TestHistoryError:
    """错误枚举测试"""

    def test_all_errors_have_correct_http_status(self):
        from app.history import HistoryErrorCode
        assert HistoryErrorCode.INVALID_CODE.value[1] == 400
        assert HistoryErrorCode.STOCK_NOT_FOUND.value[1] == 404
        assert HistoryErrorCode.FETCH_TIMEOUT.value[1] == 408
        assert HistoryErrorCode.RATE_LIMITED.value[1] == 429
        assert HistoryErrorCode.INTERNAL_ERROR.value[1] == 500

    def test_history_error_to_dict(self):
        from app.history import HistoryError, HistoryErrorCode
        err = HistoryError(HistoryErrorCode.STOCK_NOT_FOUND)
        d = err.to_dict()
        assert d["code"] == "STOCK_NOT_FOUND"
        assert "未找到" in d["message"]


# ============================================================================
# B8 补充测试：输入校验、错误映射、mock 确定性、API 契约
# ============================================================================


class TestInputValidation:
    """B4 输入校验测试"""

    def test_period_whitelist(self):
        from app.history import _validate_period, HistoryError
        assert _validate_period("daily") == "daily"
        assert _validate_period("weekly") == "weekly"
        assert _validate_period("monthly") == "monthly"
        with pytest.raises(HistoryError):
            _validate_period("hourly")
        with pytest.raises(HistoryError):
            _validate_period("")

    def test_adjust_whitelist(self):
        from app.history import _validate_adjust, HistoryError
        assert _validate_adjust("qfq") == "qfq"
        assert _validate_adjust("none") == "none"
        with pytest.raises(HistoryError):
            _validate_adjust("hfq")
        with pytest.raises(HistoryError):
            _validate_adjust("")

    def test_date_range_valid(self):
        from app.history import _validate_date_range
        s, e = _validate_date_range("2020-01-01", "2025-06-18")
        assert s == "2020-01-01"
        assert e == "2025-06-18"

    def test_date_range_start_after_end(self):
        from app.history import _validate_date_range, HistoryError
        with pytest.raises(HistoryError):
            _validate_date_range("2025-01-01", "2020-01-01")

    def test_date_range_bad_format(self):
        from app.history import _validate_date_range, HistoryError
        with pytest.raises(HistoryError):
            _validate_date_range("abcd", "2025-01-01")
        with pytest.raises(HistoryError):
            _validate_date_range("2025-13-01", "2025-01-01")

    def test_date_range_span_limit(self):
        from app.history import _validate_date_range, HistoryError
        with pytest.raises(HistoryError):
            _validate_date_range("1900-01-01", "2025-01-01")


class TestMapAkshareError:
    """B8 _map_akshare_error 关键字表驱动测试"""

    def test_network_errors(self):
        from app.history import _map_akshare_error, HistoryErrorCode
        keywords = [
            "proxy error", "connection refused", "disconnected",
            "maxretry", "network unreachable", "dns resolve failed",
            "timeout occurred", "请求超时",
        ]
        for kw in keywords:
            err = _map_akshare_error(Exception(kw))
            assert err.code == HistoryErrorCode.SOURCE_UNAVAILABLE, f"keyword '{kw}' should map to SOURCE_UNAVAILABLE"

    def test_not_found_errors(self):
        from app.history import _map_akshare_error, HistoryErrorCode
        for kw in ["not found", "不存在", "404"]:
            err = _map_akshare_error(Exception(kw))
            assert err.code == HistoryErrorCode.STOCK_NOT_FOUND, f"keyword '{kw}' should map to STOCK_NOT_FOUND"

    def test_rate_limit_errors(self):
        from app.history import _map_akshare_error, HistoryErrorCode
        for kw in ["429", "rate limited", "请求频繁"]:
            err = _map_akshare_error(Exception(kw))
            assert err.code == HistoryErrorCode.RATE_LIMITED, f"keyword '{kw}' should map to RATE_LIMITED"

    def test_unknown_errors(self):
        from app.history import _map_akshare_error, HistoryErrorCode
        err = _map_akshare_error(Exception("something unexpected"))
        assert err.code == HistoryErrorCode.INTERNAL_ERROR


class TestMockSeedCandles:
    """B8 _mock_seed_candles 确定性测试"""

    def test_returns_result_for_known_seed(self):
        from app.history import _mock_seed_candles
        result = _mock_seed_candles("600519", "daily", "2025-01-01", "2025-01-10")
        assert result is not None
        assert result.code == "600519"
        assert result.name == "贵州茅台"
        assert result.source == "mock_seed"
        assert len(result.candles) > 0

    def test_returns_none_for_unknown_code(self):
        from app.history import _mock_seed_candles
        result = _mock_seed_candles("999999", "daily", "2025-01-01", "2025-01-10")
        assert result is None

    def test_deterministic_same_inputs(self):
        from app.history import _mock_seed_candles
        r1 = _mock_seed_candles("600519", "daily", "2025-01-01", "2025-01-10")
        r2 = _mock_seed_candles("600519", "daily", "2025-01-01", "2025-01-10")
        assert r1.candles == r2.candles

    def test_different_codes_differ(self):
        from app.history import _mock_seed_candles
        r1 = _mock_seed_candles("600519", "daily", "2025-01-01", "2025-01-10")
        r2 = _mock_seed_candles("000001", "daily", "2025-01-01", "2025-01-10")
        assert r1.candles != r2.candles

    def test_candle_shape_has_required_keys(self):
        from app.history import _mock_seed_candles
        result = _mock_seed_candles("600519", "daily", "2025-01-01", "2025-01-03")
        assert result is not None
        for c in result.candles:
            assert "trade_date" in c
            assert "open" in c
            assert "high" in c
            assert "low" in c
            assert "close" in c
            assert "volume" in c


class TestToDictContract:
    """B8 HistoryResult.to_dict() 输出契约测试（PRD §5.3.1）"""

    def test_to_dict_has_meta_and_time(self):
        from app.history import HistoryResult
        result = HistoryResult(
            code="600519", name="贵州茅台", period="daily", adjust="qfq",
            start_date="2025-01-01", end_date="2025-01-10",
            total_count=5, latest_close=1800.0, latest_change_pct=1.5,
            candles=[
                {"trade_date": "2025-01-06", "open": 1780, "high": 1810, "low": 1770, "close": 1800, "volume": 100000},
                {"trade_date": "2025-01-07", "open": 1800, "high": 1820, "low": 1790, "close": 1810, "volume": 120000},
            ],
            industry="白酒", market_cap=20000.0, turnover=1.2,
        )
        d = result.to_dict()

        # meta 嵌套对象
        assert "meta" in d
        assert d["meta"]["total_count"] == 5
        assert d["meta"]["latest_close"] == 1800.0
        assert d["meta"]["start_date"] == "2025-01-01"

        # F5 新增字段
        assert d["meta"]["industry"] == "白酒"
        assert d["meta"]["market_cap"] == 20000.0
        assert d["meta"]["turnover"] == 1.2

        # candle 用 time 不是 trade_date
        assert len(d["candles"]) == 2
        for c in d["candles"]:
            assert "time" in c
            assert "trade_date" not in c
            assert "open" in c
            assert "close" in c

    def test_to_dict_accepts_time_key(self):
        """如果 candle 已有 time 键，to_dict 应直接使用"""
        from app.history import HistoryResult
        result = HistoryResult(
            code="600519", name="贵州茅台", period="daily", adjust="qfq",
            start_date="2025-01-01", end_date="2025-01-10",
            total_count=1, latest_close=1800.0, latest_change_pct=0.0,
            candles=[{"time": "2025-01-06", "open": 1780, "high": 1810, "low": 1770, "close": 1800, "volume": 100000}],
        )
        d = result.to_dict()
        assert d["candles"][0]["time"] == "2025-01-06"


class TestFetchHistoryIntegration:
    """B8 fetch_history 集成测试（mock akshare，验证端到端契约）"""

    def test_fetch_history_with_mock_akshare(self):
        """mock akshare 返回 → fetch_history 应返回含 time/meta 的正确结构"""
        from app.history import fetch_history

        # _fetch_from_akshare 已经调用 _normalize_columns，返回标准化列名
        mock_df = pd.DataFrame({
            "trade_date": ["2025-01-06", "2025-01-07"],
            "open": [1780.0, 1800.0],
            "high": [1810.0, 1820.0],
            "low": [1770.0, 1790.0],
            "close": [1800.0, 1810.0],
            "volume": [100000, 120000],
        })

        with patch("app.history._fetch_from_akshare", return_value=mock_df):
            with patch("app.history._read_from_cache", return_value=None):
                with patch("app.history._save_to_cache"):
                    with patch("app.history._get_stock_name_from_info", return_value="贵州茅台"):
                        result = fetch_history("600519", "daily", "qfq", "2025-01-06", "2025-01-07")

        assert result.code == "600519"
        assert result.name == "贵州茅台"
        assert result.total_count == 2
        assert len(result.candles) == 2

        d = result.to_dict()
        assert "meta" in d
        assert d["meta"]["total_count"] == 2
        assert d["candles"][0]["time"] == "2025-01-06"
        for c in d["candles"]:
            assert "trade_date" not in c
