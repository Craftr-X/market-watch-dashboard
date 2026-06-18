/**
 * StatsPanel — 区间统计面板
 */

import { Candle } from "@/hooks/useStockHistory";

interface StatsPanelProps {
  candles: Candle[];
}

function cnPct(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function pctClass(value: number) {
  if (value > 0) return "up";
  if (value < 0) return "down";
  return "flat";
}

function formatMoney(value: number) {
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(2)}亿`;
  if (value >= 10_000) return `${(value / 10_000).toFixed(0)}万`;
  return value.toFixed(0);
}

export default function StatsPanel({ candles }: StatsPanelProps) {
  if (!candles || candles.length === 0) return null;

  const first = candles[0];
  const last = candles[candles.length - 1];

  // 区间涨跌幅（基准为首日收盘价，非开盘价；至少 2 根 K 线才算）
  const periodChangePct =
    first.close > 0 && candles.length > 1
      ? ((last.close - first.close) / first.close) * 100
      : 0;

  // 期间最高/最低
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const maxHigh = Math.max(...highs);
  const minLow = Math.min(...lows);

  // 平均成交量
  const avgVolume = candles.reduce((s, c) => s + c.volume, 0) / candles.length;

  // 平均成交额
  const avgTurnover =
    candles.reduce((s, c) => s + Math.abs(c.close * c.volume), 0) /
    candles.length;

  return (
    <div className="statsPanel">
      <div className="statItem">
        <span className="statLabel">区间涨跌</span>
        <strong className={pctClass(periodChangePct)}>
          {cnPct(periodChangePct)}
        </strong>
      </div>
      <div className="statItem">
        <span className="statLabel">期间最高</span>
        <strong>{maxHigh.toFixed(2)}</strong>
      </div>
      <div className="statItem">
        <span className="statLabel">期间最低</span>
        <strong>{minLow.toFixed(2)}</strong>
      </div>
      <div className="statItem">
        <span className="statLabel">平均成交量</span>
        <strong>{formatMoney(avgVolume)}手</strong>
      </div>
      <div className="statItem">
        <span className="statLabel">最新收盘</span>
        <strong>{last.close.toFixed(2)}</strong>
      </div>
    </div>
  );
}
