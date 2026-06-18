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
