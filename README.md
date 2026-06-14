# market-watch-dashboard

本地运行的 A 股每日行情与强势观察 Web 工具，用于市场学习与收盘复盘，不提供买卖建议。

## 功能

- 今日市场总览：上证指数、深证成指、创业板指、沪深300、中证A500、中证500
- 板块热度：行业/概念涨幅、成交额和领涨样本
- 强势观察：按涨幅、成交额、量比、板块强度和趋势计算观察分
- 风险提醒：ST/退市风险、停牌/异常、近5日涨幅过高、成交额过低等标签
- 每日复盘：自动生成市场状态、强势方向、观察样本和定投提醒
- SQLite：每日刷新后保留历史记录

## 启动后端

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

手动刷新：

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/refresh
```

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:3000
```

## API

- `GET /api/market/overview`
- `GET /api/sectors/rank`
- `GET /api/stocks/strong`
- `GET /api/stocks/risk`
- `GET /api/reports/daily`
- `POST /api/jobs/refresh`

所有接口均返回：

```json
{
  "data": {},
  "updated_at": "2026-06-14T15:30:00",
  "source": "sample-akshare-compatible",
  "risk_disclaimer": "本系统仅用于市场学习和行情复盘，不构成投资建议。个股观察不代表买入建议，投资需自行决策并承担风险。"
}
```

## 数据源说明

第一版代码保留了 AKShare/东方财富公开行情的接入位置，但为了本地首次运行稳定，当前默认使用 AKShare 兼容字段的样例数据生成 SQLite 记录。后续可在 `backend/app/data_source.py` 中替换为真实 AKShare 获取逻辑。

## 风险边界

本系统仅用于市场学习和行情复盘，不构成投资建议。个股观察不代表买入建议，投资需自行决策并承担风险。大多数情况下，基金/宽基定投不应因为一天行情改变长期计划。
