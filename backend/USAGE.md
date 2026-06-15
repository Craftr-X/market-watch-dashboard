# A股每日行情与强势观察 - 使用指南

## 项目简介

这是一个基于 AkShare 的 A 股行情监控系统，提供实时行情数据、板块热度、强势股票观察和风险预警功能。

## 功能特性

- **实时行情数据**：获取 A 股主要指数、板块和个股数据
- **板块热度分析**：行业板块涨跌幅排行
- **强势股票观察**：基于评分算法筛选强势股 Top 20
- **风险预警**：识别 ST、停牌、涨幅过高等风险股票
- **每日复盘**：自动生成市场复盘摘要
- **定时任务**：每个交易日 15:30 自动刷新数据

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

- **前端页面**：http://localhost:3000
- **API 文档**：http://localhost:8000/docs
- **定时任务状态**：http://localhost:8000/api/scheduler/status

## API 接口

### 市场概览
```
GET /api/market/overview
```
返回主要指数行情和市场状态（偏强/分化/偏弱）

### 板块排行
```
GET /api/sectors/rank
```
返回行业板块涨跌幅排行 Top 10

### 强势股票
```
GET /api/stocks/strong
```
返回评分最高的 20 只强势股票

### 风险股票
```
GET /api/stocks/risk
```
返回有风险标签的股票（ST、停牌、涨幅过高等）

### 每日报告
```
GET /api/reports/daily
```
返回每日复盘摘要

### 手动刷新
```
POST /api/jobs/refresh
```
手动触发数据刷新

### 定时任务状态
```
GET /api/scheduler/status
```
查看定时任务运行状态

## 数据源

使用 [AkShare](https://github.com/akfamily/akshare) 获取 A 股行情数据：

- **指数数据**：新浪接口（stock_zh_index_spot_sina）
- **板块数据**：新浪接口（stock_sector_spot）
- **个股数据**：新浪接口（stock_zh_a_spot）

## 定时任务配置

默认配置：每个交易日 15:30 自动刷新（北京时间）

配置文件：`backend/app/scheduler.py`

```python
scheduler.add_job(
    refresh_market,
    trigger=CronTrigger(
        day_of_week="mon-fri",
        hour=15,
        minute=30,
        timezone="Asia/Shanghai",
    ),
    args=[store],
    id="daily_refresh",
    name="每日行情刷新",
)
```

## 评分算法

强势股票评分基于以下维度：

1. **涨跌幅**（30%）：当日涨幅越高，得分越高
2. **成交额**（20%）：成交额越大，流动性越好
3. **量比**（20%）：量比越高，资金关注度越高
4. **板块强度**（20%）：所属板块涨幅越高，加分越多
5. **趋势突破**（10%）：突破关键位置加分

风险惩罚：
- ST 股票：-65 分
- 停牌股票：-35 分
- 近 5 日涨幅过高：-15 分
- 成交额过低：-18 分
- 高位放量下跌：-20 分

## 注意事项

1. **数据延迟**：新浪接口有 15-30 秒延迟，非 Level 2 实时数据
2. **网络环境**：需要稳定的网络连接访问数据源
3. **交易时间**：非交易时间获取的是上一个交易日的数据
4. **风险提示**：本系统仅用于学习和复盘，不构成投资建议

## 常见问题

### Q: 数据获取失败怎么办？

A: 检查网络连接，确保能访问新浪财经。如果网络受限，可能需要配置代理。

### Q: 如何修改定时任务时间？

A: 编辑 `backend/app/scheduler.py` 中的 CronTrigger 参数。

### Q: 如何添加更多指数？

A: 编辑 `backend/app/data_source.py` 中的 `TRACKED_INDICES` 字典。

### Q: 数据存储在哪里？

A: 默认存储在 `backend/data/market_watch.db`（SQLite 数据库）

## 开发指南

### 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置文件
│   ├── data_source.py     # 数据源（AkShare）
│   ├── main.py            # FastAPI 应用
│   ├── reporting.py       # 报告生成
│   ├── scheduler.py       # 定时任务
│   ├── scoring.py         # 评分算法
│   └── storage.py         # 数据存储（SQLite）
├── tests/
├── data/                  # 数据库文件
├── requirements.txt
└── USAGE.md
```

### 运行测试

```bash
pytest tests/
```

### 代码规范

- 使用 Python 3.10+ 类型注解
- 遵循 PEP 8 代码规范
- 使用 pytest 编写测试

## 更新日志

### v0.2.0 (2026-06-15)
- 集成 AkShare 真实数据源
- 添加定时任务调度器
- 优化错误处理和重试机制
- 新增定时任务状态 API

### v0.1.0 (2026-06-14)
- 初始版本
- 基础架构搭建
- 示例数据展示
