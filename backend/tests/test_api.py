from fastapi.testclient import TestClient

from app.main import create_app


def _make_db_url(tmp_path) -> str:
    """构造跨平台兼容的 SQLite URL（Windows 路径需特殊处理）"""
    db_path = tmp_path / "market.db"
    # Windows 路径需要转换为 POSIX 格式，并确保 URL 格式正确
    return f"sqlite:///{db_path.as_posix()}"


def test_api_responses_include_metadata_and_disclaimer(tmp_path):
    app = create_app(database_url=_make_db_url(tmp_path))
    client = TestClient(app)

    refresh = client.post("/api/jobs/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["data"]["status"] == "ok"

    response = client.get("/api/stocks/strong")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]
    assert body["updated_at"]
    assert body["source"] == "akshare"
    assert "不构成投资建议" in body["risk_disclaimer"]
    assert {"code", "name", "score", "risk_note"} <= set(body["data"][0])


def test_daily_report_answers_market_learning_questions(tmp_path):
    app = create_app(database_url=_make_db_url(tmp_path))
    client = TestClient(app)
    client.post("/api/jobs/refresh")

    response = client.get("/api/reports/daily")
    report = response.json()["data"]

    assert "今日市场" in report["summary"]
    assert "不因为一天行情改变长期计划" in report["summary"]
    assert report["risk_notes"]
