"""
后端单元测试：history.py 核心逻辑（不依赖 AkShare）
"""

import pytest
from datetime import date, timedelta


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
        from app.history import _date_range
        start, end = _date_range("daily")
        expected_start = (date.today() - timedelta(days=365 * 3)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == date.today().isoformat()

    def test_weekly_returns_5_years(self):
        from app.history import _date_range
        start, end = _date_range("weekly")
        expected_start = (date.today() - timedelta(days=365 * 5)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == date.today().isoformat()

    def test_monthly_returns_10_years(self):
        from app.history import _date_range
        start, end = _date_range("monthly")
        expected_start = (date.today() - timedelta(days=365 * 10)).isoformat()
        start_date = date.fromisoformat(start)
        expected = date.fromisoformat(expected_start)
        assert abs((start_date - expected).days) <= 1
        assert end == date.today().isoformat()


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
