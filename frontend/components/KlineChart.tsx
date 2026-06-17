/**
 * KlineChart — K线主图 + 均线叠加
 * 使用 lightweight-charts v4（TradingView 出品）
 */

"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  CrosshairMode,
  Time,
} from "lightweight-charts";
import { calcAllMA, MAVariants, MA_COLORS } from "@/utils/ma";

interface ChartCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface KlineChartProps {
  candles: ChartCandle[];
  showMA: Record<keyof MAVariants, boolean>;
  height?: number;
}

// lightweight-charts 颜色配置（沿用终端风格）
const CHART_COLORS = {
  background: "#090d12",
  textColor: "#8aa0b8",
  gridColor: "rgba(116, 156, 190, 0.15)",
  borderColor: "rgba(116, 156, 190, 0.22)",
  crosshairColor: "rgba(83, 214, 232, 0.5)",
  crosshairLabel: "#53d6e8",
  upColor: "#ff5f5a",
  downColor: "#39d98a",
};

export default function KlineChart({ candles, showMA, height = 420 }: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const maSeriesRef = useRef<Record<keyof MAVariants, ISeriesApi<"Line"> | null>>({
    ma5: null,
    ma10: null,
    ma20: null,
    ma60: null,
  });

  // =========================================================================
  // 初始化图表（只执行一次）
  // =========================================================================
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: CHART_COLORS.background },
        textColor: CHART_COLORS.textColor,
      },
      grid: {
        vertLines: { color: CHART_COLORS.gridColor },
        horzLines: { color: CHART_COLORS.gridColor },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: CHART_COLORS.crosshairColor,
          labelBackgroundColor: CHART_COLORS.crosshairLabel,
          width: 1,
          style: 2,
        },
        horzLine: {
          color: CHART_COLORS.crosshairColor,
          labelBackgroundColor: CHART_COLORS.crosshairLabel,
          width: 1,
          style: 2,
        },
      },
      timeScale: {
        borderColor: CHART_COLORS.borderColor,
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
      },
      rightPriceScale: {
        borderColor: CHART_COLORS.borderColor,
      },
      height,
    });

    // 主 K 线系列
    const candleSeries = chart.addCandlestickSeries({
      upColor: CHART_COLORS.upColor,
      downColor: CHART_COLORS.downColor,
      borderUpColor: CHART_COLORS.upColor,
      borderDownColor: CHART_COLORS.downColor,
      wickUpColor: CHART_COLORS.upColor,
      wickDownColor: CHART_COLORS.downColor,
    });

    // 均线系列（提前创建好，按 showMA 控制显隐）
    const maKeys: (keyof MAVariants)[] = ["ma5", "ma10", "ma20", "ma60"];
    const maSeries: Record<keyof MAVariants, ISeriesApi<"Line"> | null> = {
      ma5: null,
      ma10: null,
      ma20: null,
      ma60: null,
    };
    for (const key of maKeys) {
      maSeries[key] = chart.addLineSeries({
        color: MA_COLORS[key],
        title: key.toUpperCase() as string,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
    }

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    maSeriesRef.current = maSeries;

    // 响应式监听
    const resizeObserver = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width: Math.max(width, 320) });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      maSeriesRef.current = { ma5: null, ma10: null, ma20: null, ma60: null };
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // =========================================================================
  // 更新 K 线数据
  // =========================================================================
  useEffect(() => {
    if (!candleSeriesRef.current || !candles.length) return;

    const formatted: CandlestickData<Time>[] = candles.map((c) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSeriesRef.current.setData(formatted);
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  // =========================================================================
  // 更新均线数据（showMA 变化时）
  // =========================================================================
  useEffect(() => {
    if (!candles.length) return;

    const closeCandles = candles.map((c) => ({ time: c.time, close: c.close }));
    const maData = calcAllMA(closeCandles);

    const maKeys: (keyof MAVariants)[] = ["ma5", "ma10", "ma20", "ma60"];
    for (const key of maKeys) {
      const series = maSeriesRef.current[key];
      if (!series) continue;

      const shouldShow = showMA[key];
      const data = maData[key];

      if (shouldShow && data.length > 0) {
        const lineData: LineData<Time>[] = data.map((m: { time: string; value: number }) => ({
          time: m.time as Time,
          value: m.value,
        }));
        series.setData(lineData);
        series.applyOptions({ visible: true });
      } else {
        series.setData([]);
        series.applyOptions({ visible: false });
      }
    }
  }, [candles, showMA]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height }}
      aria-label="K线走势图表"
    />
  );
}
