# market-watch-dashboard

本地运行的 A 股每日行情与强势观察 Web 工具，用于市场学习与收盘复盘，不提供买卖建议。

## 功能

- **实时行情数据**：获取 A 股主要指数、板块和个股数据（AkShare 数据源）
- **板块热度分析**：行业板块涨跌幅排行
- **强势股票观察**：基于评分算法筛选强势股 Top 20
- **风险预警**：识别 ST、停牌、涨幅过高等风险股票
- **每日复盘**：自动生成市场复盘摘要
- **个股历史走势**：K 线图 + 均线叠加 + 成交量副图，支持日/周/月线切换、前复权/不复权（v0.3.0 新增）
- **股票搜索**：支持代码/名称模糊搜索（v0.3.0 新增）
- **自选股收藏**：本地收藏常用股票（v0.3.0 新增）
- **定时任务**：每个交易日 15:30 自动刷新数据
- **SQLite 存储**：每日刷新后保留历史记录

## 快速开始

### 方式一：使用启动脚本（Windows）

```bash
# 启动后端
start.bat

# 新窗口启动前端
start-frontend.bat
```

### 方式二：手动启动

#### 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 访问应用

- **前端页面**：http://localhost:3000
- **API 文档**：http://localhost:8000/docs
- **定时任务状态**：http://localhost:8000/api/scheduler/status

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/market/overview` | GET | 主要指数行情和市场状态 |
| `/api/sectors/rank` | GET | 行业板块涨跌幅排行 |
| `/api/stocks/strong` | GET | 强势股票 Top 20 |
| `/api/stocks/risk` | GET | 风险股票列表 |
| `/api/reports/daily` | GET | 每日复盘报告 |
| `/api/jobs/refresh` | POST | 手动刷新数据 |
| `/api/scheduler/status` | GET | 定时任务状态 |
| `/api/stocks/history` | GET | 个股历史行情（K线，支持日/周/月线、前复权/不复权） |
| `/api/stocks/search` | GET | 股票代码/名称模糊搜索 |

所有接口均返回：

```json
{
  "data": {},
  "updated_at": "2026-06-15T15:30:00",
  "source": "akshare",
  "risk_disclaimer": "本系统仅用于市场学习和行情复盘，不构成投资建议。个股观察不代表买入建议，投资需自行决策并承担风险。"
}
```

## 数据源

使用 [AkShare](https://github.com/akfamily/akshare) 获取 A 股行情数据：

- **指数数据**：新浪接口（stock_zh_index_spot_sina）
- **板块数据**：新浪接口（stock_sector_spot）
- **个股数据**：新浪接口（stock_zh_a_spot）

### 定时任务

默认配置：每个交易日 15:30 自动刷新（北京时间）

查看定时任务状态：
```bash
curl http://127.0.0.1:8000/api/scheduler/status
```

手动刷新：
```bash
curl -X POST http://127.0.0.1:8000/api/jobs/refresh
```

## 项目结构

```
market-watch-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # 配置文件
│   │   ├── data_source.py     # 数据源（AkShare）
│   │   ├── history.py         # 个股历史行情服务（v0.3.0 新增）
│   │   ├── main.py            # FastAPI 应用
│   │   ├── reporting.py       # 报告生成
│   │   ├── scheduler.py       # 定时任务（含缓存预热 v0.3.0）
│   │   ├── scoring.py         # 评分算法
│   │   ├── search.py          # 股票搜索服务（v0.3.0 新增）
│   │   └── storage.py         # 数据存储（SQLite，含 history/info 表 v0.3.0）
│   ├── tests/
│   ├── data/                  # 数据库文件
│   ├── requirements.txt
│   └── USAGE.md               # 详细使用指南
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx           # 首页
│   │   ├── styles.css
│   │   ├── components/         # 通用组件
│   │   │   ├── KlineChart.tsx        # K线图（v0.3.0）
│   │   │   ├── VolumeChart.tsx       # 成交量副图（v0.3.0）
│   │   │   ├── StockHeader.tsx        # 个股头部（v0.3.0）
│   │   │   ├── StockToolbar.tsx      # 工具栏（v0.3.0）
│   │   │   ├── StatsPanel.tsx         # 统计面板（v0.3.0）
│   │   │   ├── SearchModal.tsx        # 搜索弹层（v0.3.0）
│   │   │   ├── WatchlistButton.tsx    # 收藏按钮（v0.3.0）
│   │   │   └── ErrorCard.tsx          # 错误卡片（v0.3.0）
│   │   ├── hooks/
│   │   │   ├── useStockHistory.ts     # 历史数据 hook（v0.3.0）
│   │   │   └── useSearch.ts           # 搜索 hook（v0.3.0）
│   │   ├── store/
│   │   │   └── watchlist.ts           # Zustand 自选股（v0.3.0）
│   │   ├── utils/
│   │   │   └── ma.ts                 # 均线计算（v0.3.0）
│   │   └── stock/[code]/
│   │       └── page.tsx              # 个股详情页（v0.3.0 新路由）
│   ├── package.json
│   └── tsconfig.json
├── docs/
├── start.bat                  # 后端启动脚本
├── start-frontend.bat         # 前端启动脚本
└── README.md
```

## 评分算法

强势股票评分基于以下维度：

| 维度 | 权重 | 说明 |
|------|------|------|
| 涨跌幅 | 30% | 当日涨幅越高，得分越高 |
| 成交额 | 20% | 成交额越大，流动性越好 |
| 量比 | 20% | 量比越高，资金关注度越高 |
| 板块强度 | 20% | 所属板块涨幅越高，加分越多 |
| 趋势突破 | 10% | 突破关键位置加分 |

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

## 更新日志

### v0.3.0 (2026-06-17)
- ✅ 新增个股历史走势分析：K 线图 + 成交量副图 + MA5/10/20/60 均线
- ✅ 支持日线/周线/月线三周期切换
- ✅ 支持前复权/不复权一键切换
- ✅ 新增股票搜索（代码/名称模糊搜索）
- ✅ 新增自选股收藏（localStorage 持久化）
- ✅ 新增 `stock_history` / `stock_info` SQLite 表
- ✅ 新增 `/api/stocks/history` 和 `/api/stocks/search` API
- ✅ 新增定时缓存预热任务（周线/月线/股票列表同步）
- ✅ 新增后端单元测试（`tests/test_history.py`）
- ✅ 前端新增 `lightweight-charts` 图表库
- ✅ 新增 Zustand 状态管理（自选股）
- ✅ 更新 `tsconfig.json` 路径别名 `@/*`
- ✅ `npm run build` 通过，无 TypeScript 错误

### v0.2.0 (2026-06-15)
- ✅ 集成 AkShare 真实数据源
- ✅ 添加定时任务调度器（每个交易日 15:30 自动刷新）
- ✅ 优化错误处理和重试机制
- ✅ 新增定时任务状态 API
- ✅ 更新使用文档

### v0.1.0 (2026-06-14)
- 初始版本
- 基础架构搭建
- 示例数据展示

## 风险边界

本系统仅用于市场学习和行情复盘，不构成投资建议。个股观察不代表买入建议，投资需自行决策并承担风险。大多数情况下，基金/宽基定投不应因为一天行情改变长期计划。
