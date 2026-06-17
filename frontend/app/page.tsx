"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  RefreshCw,
  Search,
  ShieldAlert,
  Signal,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import SearchModal from "@/components/SearchModal";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

type Envelope<T> = {
  data: T;
  updated_at: string | null;
  source: string;
  risk_disclaimer: string;
};

type IndexItem = {
  index_code: string;
  index_name: string;
  close: number;
  change_pct: number;
  turnover: number;
};

type Sector = {
  sector_name: string;
  sector_type: string;
  change_pct: number;
  turnover: number;
  leading_stocks: string;
};

type Stock = {
  code: string;
  name: string;
  change_pct: number;
  turnover: number;
  volume_ratio: number;
  industry: string;
  concept: string;
  score: number;
  strength_reason: string;
  risk_tags: string[];
  risk_note: string;
};

type Report = {
  summary: string;
  strong_sectors: string[];
  strong_stocks: string[];
  risk_notes: string[];
};

type DashboardData = {
  overview: Envelope<{ indices: IndexItem[]; market_state: string }>;
  sectors: Envelope<Sector[]>;
  strong: Envelope<Stock[]>;
  risk: Envelope<Stock[]>;
  report: Envelope<Report>;
};

async function fetchJson<T>(path: string): Promise<Envelope<T>> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Request failed: ${path}`);
  return response.json();
}

function cnPct(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function money(value: number) {
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(1)}亿`;
  return `${(value / 10_000).toFixed(0)}万`;
}

function pctClass(value: number) {
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "flat";
}

function scoreClass(value: number) {
  if (value >= 75) return "score scoreHot";
  if (value >= 45) return "score scoreWarm";
  return "score";
}

export default function Page() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [overview, sectors, strong, risk, report] = await Promise.all([
        fetchJson<{ indices: IndexItem[]; market_state: string }>("/api/market/overview"),
        fetchJson<Sector[]>("/api/sectors/rank"),
        fetchJson<Stock[]>("/api/stocks/strong"),
        fetchJson<Stock[]>("/api/stocks/risk"),
        fetchJson<Report>("/api/reports/daily"),
      ]);
      setData({ overview, sectors, strong, risk, report });
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      await fetch(`${API_BASE}/api/jobs/refresh`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "刷新失败");
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const updatedAt = useMemo(() => data?.overview.updated_at?.replace("T", " ") ?? "--", [data]);
  const avgIndexChange = useMemo(() => {
    const indices = data?.overview.data.indices ?? [];
    if (!indices.length) return 0;
    return indices.reduce((sum, item) => sum + item.change_pct, 0) / indices.length;
  }, [data]);
  const topSectors = useMemo(() => (data?.sectors.data ?? []).slice(0, 3), [data]);
  const riskCount = data?.risk.data.length ?? 0;
  const hotStock = data?.strong.data[0];

  return (
    <main className="terminalPage">
      <header className="terminalHeader">
        <div className="brandBlock">
          <div className="eyebrow">
            <Signal size={15} />
            MARKET WATCH TERMINAL
          </div>
          <h1>A股每日行情与强势观察</h1>
          <p>收盘后复盘 · 市场强弱 · 板块热度 · 强势观察 · 风险过滤</p>
        </div>
        <div className="headerActions">
          <div className="metaPill">
            <Database size={15} />
            <span>{data?.overview.source ?? "loading"}</span>
          </div>
          <div className="metaPill">
            <Activity size={15} />
            <span>{updatedAt}</span>
          </div>
          <button className="refresh" onClick={() => setShowSearch(true)} title="搜索股票" aria-label="搜索股票">
            <Search size={18} />
            搜索
          </button>
          <button className="refresh" onClick={refresh} disabled={loading} title="刷新行情">
            <RefreshCw size={18} className={loading ? "spin" : ""} />
            {loading ? "同步中" : "刷新行情"}
          </button>
        </div>
      </header>

      {error && <div className="notice error">{error}</div>}
      {data && (
        <div className="notice">
          <ShieldAlert size={18} />
          <span>{data.overview.risk_disclaimer}</span>
        </div>
      )}

      <section className="commandGrid">
        <article className="marketStatePanel">
          <div className="panelGlow" />
          <div className="label">今日市场状态</div>
          <strong>{data?.overview.data.market_state ?? (loading ? "加载中" : "--")}</strong>
          <span className={pctClass(avgIndexChange)}>指数均值 {cnPct(avgIndexChange)}</span>
          <div className="marketScale">
            <i />
          </div>
        </article>

        <div className="telemetryGrid">
          <TelemetryCard icon={<TrendingUp size={18} />} label="强势方向" value={topSectors.map((s) => s.sector_name).join(" / ") || "--"} tone="cyan" />
          <TelemetryCard icon={<Zap size={18} />} label="观察榜首" value={hotStock ? `${hotStock.name} ${hotStock.score.toFixed(1)}` : "--"} tone="red" />
          <TelemetryCard icon={<AlertTriangle size={18} />} label="风险样本" value={`${riskCount} 个`} tone="amber" />
        </div>

        <div className="indexTicker">
          {(data?.overview.data.indices ?? []).map((item) => (
            <article className="tickerCard" key={item.index_code}>
              <div>
                <span>{item.index_name}</span>
                <em>{item.index_code}</em>
              </div>
              <strong>{item.close.toFixed(2)}</strong>
              <b className={pctClass(item.change_pct)}>{cnPct(item.change_pct)}</b>
              <small>成交 {money(item.turnover)}</small>
            </article>
          ))}
          {!data && Array.from({ length: 6 }).map((_, index) => <article className="tickerCard skeleton" key={index} />)}
        </div>
      </section>

      <section className="twoCol">
        <Panel icon={<BarChart3 size={20} />} title="板块热度" aside="行业 / 概念涨幅榜">
          <div className="tableWrap compact">
            <table>
              <thead>
                <tr>
                  <th>板块</th>
                  <th>类型</th>
                  <th>涨跌幅</th>
                  <th>成交额</th>
                  <th>领涨样本</th>
                </tr>
              </thead>
              <tbody>
                {data?.sectors.data.map((sector) => (
                  <tr key={`${sector.sector_type}-${sector.sector_name}`}>
                    <td><span className="nameCell">{sector.sector_name}</span></td>
                    <td><span className="tag">{sector.sector_type}</span></td>
                    <td className={pctClass(sector.change_pct)}>{cnPct(sector.change_pct)}</td>
                    <td>{money(sector.turnover)}</td>
                    <td>{sector.leading_stocks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel icon={<ShieldAlert size={20} />} title="风险雷达" aside="固定展示，不隐藏">
          <div className="riskList">
            {(data?.risk.data ?? []).map((stock) => (
              <article className="riskItem" key={stock.code}>
                <div>
                  <span>{stock.code}</span>
                  <strong>{stock.name}</strong>
                </div>
                <b className={pctClass(stock.change_pct)}>{cnPct(stock.change_pct)}</b>
                <p>{stock.risk_tags.join("、")}</p>
              </article>
            ))}
            {data?.risk.data.length === 0 && <p className="empty">暂无突出风险标签，但仍需控制仓位和预期。</p>}
          </div>
        </Panel>
      </section>

      <Panel icon={<TrendingUp size={20} />} title="强势观察 Top 20" aside="观察对象，不代表买入建议">
        <div className="tableWrap strongTable">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>代码</th>
                <th>名称</th>
                <th>涨跌幅</th>
                <th>成交额</th>
                <th>量比</th>
                <th>行业/概念</th>
                <th>观察分</th>
                <th>强势原因</th>
                <th>风险提示</th>
              </tr>
            </thead>
            <tbody>
              {data?.strong.data.map((stock, index) => (
                <tr key={stock.code}>
                  <td><span className="rank">{index + 1}</span></td>
                  <td className="codeCell">
                    <Link href={`/stock/${stock.code}?period=daily&adjust=qfq`} className="stockCodeLink">
                      {stock.code}
                    </Link>
                  </td>
                  <td><span className="nameCell">{stock.name}</span></td>
                  <td className={pctClass(stock.change_pct)}>{cnPct(stock.change_pct)}</td>
                  <td>{money(stock.turnover)}</td>
                  <td>{stock.volume_ratio.toFixed(1)}</td>
                  <td>{stock.industry} / {stock.concept}</td>
                  <td><span className={scoreClass(stock.score)}>{stock.score.toFixed(1)}</span></td>
                  <td>{stock.strength_reason}</td>
                  <td>{stock.risk_note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel icon={<AlertTriangle size={20} />} title="每日复盘" aside="学习与长期计划">
        <div className="report">
          <p>{data?.report.data.summary ?? "正在生成复盘摘要..."}</p>
          <div className="riskChips">
            {(data?.report.data.risk_notes ?? []).map((note) => (
              <span key={note}>{note}</span>
            ))}
          </div>
        </div>
      </Panel>

      {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}
    </main>
  );
}

function TelemetryCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone: "cyan" | "red" | "amber";
}) {
  return (
    <article className={`telemetryCard ${tone}`}>
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Panel({
  title,
  icon,
  aside,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  aside?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panelTitle">
        <div>
          {icon}
          <h2>{title}</h2>
        </div>
        {aside && <span>{aside}</span>}
      </div>
      {children}
    </section>
  );
}
