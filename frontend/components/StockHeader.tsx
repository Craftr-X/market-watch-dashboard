/**
 * StockHeader — 个股头部信息栏
 */

import { HistoryMeta } from "@/hooks/useStockHistory";

interface StockHeaderProps {
  code: string;
  name: string;
  meta: HistoryMeta;
}

function pctClass(value: number) {
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "flat";
}

function formatPct(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatPrice(value: number) {
  if (value >= 10000) return `${(value / 10000).toFixed(2)}万`;
  return value.toFixed(2);
}

function formatMarketCap(value: number) {
  if (value <= 0) return "-";
  if (value >= 100_000_000_000) return `${(value / 100_000_000_000).toFixed(0)}亿`;
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(1)}亿`;
  if (value >= 10_000) return `${(value / 10_000).toFixed(0)}万`;
  return value.toFixed(0);
}

export default function StockHeader({ code, name, meta }: StockHeaderProps) {
  const pct = meta.latest_change_pct;

  return (
    <header className="stockHeader">
      <div className="stockTitle">
        <span className="stockCode">{code}</span>
        <h1 className="stockName">{name}</h1>
      </div>

      <div className="stockPrice">
        <strong className={pctClass(pct)}>
          {formatPrice(meta.latest_close)}
        </strong>
        <b className={pctClass(pct)}>{formatPct(pct)}</b>
      </div>

      <div className="stockMeta">
        {meta.industry && (
          <span className="metaItem">
            <em>行业</em>
            <span>{meta.industry}</span>
          </span>
        )}
        {meta.market_cap > 0 && (
          <span className="metaItem">
            <em>总市值</em>
            <span>{formatMarketCap(meta.market_cap)}</span>
          </span>
        )}
        {meta.turnover > 0 && (
          <span className="metaItem">
            <em>换手率</em>
            <span>{meta.turnover.toFixed(2)}%</span>
          </span>
        )}
        <span className="metaItem">
          <em>区间</em>
          <span>
            {meta.start_date} ~ {meta.end_date}
          </span>
        </span>
        <span className="metaItem">
          <em>数据量</em>
          <span>{meta.total_count} 根</span>
        </span>
      </div>
    </header>
  );
}
