/**
 * 个股历史行情数据请求 Hook
 */

import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export type Period = "daily" | "weekly" | "monthly";
export type Adjust = "qfq" | "none";

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoryMeta {
  start_date: string;
  end_date: string;
  total_count: number;
  latest_close: number;
  latest_change_pct: number;
}

export interface HistoryData {
  code: string;
  name: string;
  period: Period;
  adjust: Adjust;
  meta: HistoryMeta;
  candles: Candle[];
}

export interface HistoryResponse {
  data: HistoryData;
  updated_at: string;
  source: string;
  risk_disclaimer: string;
}

interface UseStockHistoryReturn {
  data: HistoryData | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useStockHistory(
  code: string,
  period: Period = "daily",
  adjust: Adjust = "qfq"
): UseStockHistoryReturn {
  const [data, setData] = useState<HistoryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!code) return;

    setLoading(true);
    setError(null);

    const controller = new AbortController();
    // 60 秒超时兜底
    const timeout = setTimeout(() => controller.abort(), 60_000);

    const url = `${API_BASE}/api/stocks/history?code=${encodeURIComponent(code)}&period=${period}&adjust=${adjust}`;

    fetch(url, { signal: controller.signal })
      .then((res) => {
        clearTimeout(timeout);
        if (!res.ok) {
          return res.json().then((e) => Promise.reject(e));
        }
        return res.json();
      })
      .then((json: HistoryResponse) => {
        setData(json.data);
      })
      .catch((err: Error) => {
        clearTimeout(timeout);
        if (err.name === "AbortError") {
          setError("数据获取超时（60秒），请检查网络后重试");
        } else if (err && typeof err === "object" && "detail" in err) {
          const e = err as { detail?: { code?: string; message?: string } };
          if (e.detail?.code === "STOCK_NOT_FOUND") {
            setError(`未找到股票 ${code}，请检查代码是否正确`);
          } else if (e.detail?.code === "RATE_LIMITED") {
            setError("请求过于频繁，请 30 秒后重试");
          } else {
            setError(e.detail?.message || "加载失败，请重试");
          }
        } else {
          setError("网络错误，请检查后端是否运行");
        }
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      controller.abort();
      clearTimeout(timeout);
    };
  }, [code, period, adjust, tick]);

  return { data, loading, error, refetch };
}
