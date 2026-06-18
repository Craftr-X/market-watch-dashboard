/**
 * StockToolbar — 周期 / 复权 / 均线切换工具栏
 */

import { Period, Adjust } from "@/hooks/useStockHistory";
import { MAVariants } from "@/utils/ma";

interface StockToolbarProps {
  period: Period;
  adjust: Adjust;
  showMA: Record<keyof MAVariants, boolean>;
  onPeriodChange: (p: Period) => void;
  onAdjustChange: (a: Adjust) => void;
  onMAChange: (key: keyof MAVariants, visible: boolean) => void;
}

const PERIODS: { value: Period; label: string }[] = [
  { value: "daily", label: "日线" },
  { value: "weekly", label: "周线" },
  { value: "monthly", label: "月线" },
];

const ADJUSTS: { value: Adjust; label: string }[] = [
  { value: "qfq", label: "前复权" },
  { value: "none", label: "不复权" },
];

const MA_KEYS: (keyof MAVariants)[] = ["ma5", "ma10", "ma20", "ma60"];

export default function StockToolbar({
  period,
  adjust,
  showMA,
  onPeriodChange,
  onAdjustChange,
  onMAChange,
}: StockToolbarProps) {
  return (
    <div className="stockToolbar">
      {/* 周期切换 */}
      <div className="toolGroup">
        <span className="toolLabel">周期</span>
        <div className="btnGroup">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              className={`toolBtn${period === p.value ? " active" : ""}`}
              onClick={() => onPeriodChange(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* 复权切换 */}
      <div className="toolGroup">
        <span className="toolLabel">复权</span>
        <div className="btnGroup">
          {ADJUSTS.map((a) => (
            <button
              key={a.value}
              className={`toolBtn${adjust === a.value ? " active" : ""}`}
              onClick={() => onAdjustChange(a.value)}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      {/* 均线显示切换 */}
      <div className="toolGroup maGroup">
        <span className="toolLabel">均线</span>
        <div className="btnGroup">
          {MA_KEYS.map((key) => (
            <button
              key={key}
              className={`toolBtn maBtn${showMA[key] ? " active" : ""}`}
              onClick={() => onMAChange(key, !showMA[key])}
            >
              {(key as string).toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
