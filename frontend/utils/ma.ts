/**
 * 均线计算工具
 * 从 K 线数据实时计算 MA5 / MA10 / MA20 / MA60
 */

export interface MALine {
  time: string;
  value: number;
}

export interface MAVariants {
  ma5: MALine[];
  ma10: MALine[];
  ma20: MALine[];
  ma60: MALine[];
}

/** 计算单条均线（滑动窗口 O(n)） */
export function calcMA(
  candles: Array<{ time: string; close: number }>,
  period: number
): MALine[] {
  if (candles.length < period) return [];
  const result: MALine[] = [];
  let sum = 0;
  // 初始化窗口
  for (let i = 0; i < period; i++) {
    sum += candles[i].close;
  }
  result.push({ time: candles[period - 1].time, value: parseFloat((sum / period).toFixed(2)) });
  // 滑动
  for (let i = period; i < candles.length; i++) {
    sum += candles[i].close - candles[i - period].close;
    result.push({ time: candles[i].time, value: parseFloat((sum / period).toFixed(2)) });
  }
  return result;
}

/** 计算所有均线 */
export function calcAllMA(
  candles: Array<{ time: string; close: number }>
): MAVariants {
  return {
    ma5: calcMA(candles, 5),
    ma10: calcMA(candles, 10),
    ma20: calcMA(candles, 20),
    ma60: calcMA(candles, 60),
  };
}

/** 根据周期判断该显示哪些均线 */
export function defaultVisibleMA(
  period: "daily" | "weekly" | "monthly"
): Record<keyof MAVariants, boolean> {
  if (period === "daily") {
    return { ma5: true, ma10: true, ma20: true, ma60: true };
  }
  if (period === "weekly") {
    return { ma5: true, ma10: true, ma20: false, ma60: false };
  }
  // monthly: 只显示 MA5
  return { ma5: true, ma10: false, ma20: false, ma60: false };
}

export const MA_COLORS: Record<keyof MAVariants, string> = {
  ma5: "#e2e8f0",   // 白色（灰白）
  ma10: "#f6c85f",  // 黄色
  ma20: "#a855f7",   // 紫色
  ma60: "#39d98a",   // 绿色
};
