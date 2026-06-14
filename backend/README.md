# FastAPI 后端

启动：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

刷新数据：

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/refresh
```
