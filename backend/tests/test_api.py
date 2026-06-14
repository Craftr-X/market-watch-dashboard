from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_api_responses_include_metadata_and_disclaimer(tmp_path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'market.db'}")
    client = TestClient(app)

    refresh = client.post("/api/jobs/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["data"]["status"] == "ok"

    response = client.get("/api/stocks/strong")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]
    assert body["updated_at"]
    assert body["source"] == "sample-akshare-compatible"
    assert "不构成投资建议" in body["risk_disclaimer"]
    assert {"code", "name", "score", "risk_note"} <= set(body["data"][0])


def test_daily_report_answers_market_learning_questions(tmp_path):
    app = create_app(database_url=f"sqlite:///{tmp_path / 'market.db'}")
    client = TestClient(app)
    client.post("/api/jobs/refresh")

    response = client.get("/api/reports/daily")
    report = response.json()["data"]

    assert "今日市场" in report["summary"]
    assert "不因为一天行情改变长期计划" in report["summary"]
    assert report["risk_notes"]
