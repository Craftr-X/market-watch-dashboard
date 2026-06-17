/**
 * 股票搜索 Hook（防抖版）
 */

import { useState, useEffect, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export interface SearchItem {
  code: string;
  name: string;
  market: string;
}

interface SearchResponse {
  data: { items: SearchItem[]; total: number };
  updated_at: string;
  source: string;
}

export function useSearch(query: string, debounceMs = 300) {
  const [results, setResults] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!query || query.trim().length < 1) {
      setResults([]);
      return;
    }

    // 清除上一个计时器
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      // 中止上一个请求
      if (abortRef.current) {
        abortRef.current.abort();
      }

      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);

      const url = `${API_BASE}/api/stocks/search?q=${encodeURIComponent(query.trim())}&limit=10`;

      fetch(url, { signal: controller.signal })
        .then((res) => {
          if (!res.ok) return Promise.reject(res);
          return res.json();
        })
        .then((json: SearchResponse) => {
          setResults(json.data.items);
        })
        .catch((err: Error) => {
          if (err.name !== "AbortError") {
            setResults([]);
          }
        })
        .finally(() => {
          setLoading(false);
        });
    }, debounceMs);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [query, debounceMs]);

  return { results, loading };
}
