/**
 * VolumeChart — 成交量副图
 * 使用 lightweight-charts histogram 系列，红色涨 / 绿色跌
 */

"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  HistogramData,
  Time,
} from "lightweight-charts";

interface VolumeCandle {
  time: string;
  open: number;
  close: number;
  volume: number;
}

interface VolumeChartProps {
  candles: VolumeCandle[];
  height?: number;
}

const CHART_COLORS = {
  background: "#090d12",
  textColor: "#8aa0b8",
  gridColor: "rgba(116, 156, 190, 0.1)",
  borderColor: "rgba(116, 156, 190, 0.22)",
  upColor: "rgba(255, 95, 90, 0.75)",   // 红色半透明
  downColor: "rgba(57, 217, 138, 0.75)", // 绿色半透明
};

export default function VolumeChart({ candles, height = 140 }: VolumeChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

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
      timeScale: {
        borderColor: CHART_COLORS.borderColor,
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
        tickMarkFormatter: (time: Time) => {
          return String(time).slice(5); // MM-DD
        },
      },
      rightPriceScale: {
        borderColor: CHART_COLORS.borderColor,
        scaleMargins: { top: 0.1, bottom: 0 },
      },
      height,
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "right",
    });

    chartRef.current = chart;
    volumeSeriesRef.current = volumeSeries;

    // 响应式
    const resizeObserver = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width: Math.max(width, 320) });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      volumeSeriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // =========================================================================
  // 更新成交量数据
  // =========================================================================
  useEffect(() => {
    if (!volumeSeriesRef.current || !candles.length) return;

    const formatted: HistogramData<Time>[] = candles.map((c) => ({
      time: c.time as Time,
      value: c.volume,
      color: c.close >= c.open ? CHART_COLORS.upColor : CHART_COLORS.downColor,
    }));

    volumeSeriesRef.current.setData(formatted);
  }, [candles]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height }}
      aria-label="成交量副图"
    />
  );
}
