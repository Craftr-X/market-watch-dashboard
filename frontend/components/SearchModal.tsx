/**
 * SearchModal — 股票搜索弹层
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { Search, X } from "lucide-react";
import { useSearch, SearchItem } from "@/hooks/useSearch";

interface SearchModalProps {
  onClose: () => void;
}

export default function SearchModal({ onClose }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const { results, loading } = useSearch(query);

  // 全局 Esc 键关闭（不仅限于 input 聚焦时）
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="searchOverlay" onClick={onClose}>
      <div className="searchModal" onClick={(e) => e.stopPropagation()}>
        {/* 搜索输入框 */}
        <div className="searchInputRow">
          <Search size={18} className="searchIcon" />
          <input
            autoFocus
            className="searchInput"
            placeholder="输入股票代码或名称，如 600519 / 茅台"
            value={query}
            onChange={(e) => setQuery(e.target.value)}

          />
          {query && (
            <button
              className="searchClear"
              onClick={() => setQuery("")}
              aria-label="清空搜索"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* 搜索结果列表 */}
        <div className="searchResults">
          {loading && (
            <div className="searchState">
              <span className="spinner" />
              搜索中...
            </div>
          )}

          {!loading && query && results.length === 0 && (
            <div className="searchState searchEmpty">
              未找到 &ldquo;{query}&rdquo;，请检查代码或名称
            </div>
          )}

          {!loading &&
            results.map((item: SearchItem) => (
              <Link
                key={item.code}
                href={`/stock/${item.code}?period=daily&adjust=qfq`}
                className="searchResultItem"
                onClick={onClose}
              >
                <span className="resultCode">{item.code}</span>
                <span className="resultName">{item.name}</span>
                <span className="resultMarket">
                  {item.market === "sh" ? "沪市" : "深市"}
                </span>
              </Link>
            ))}

          {!query && (
            <div className="searchHint">
              输入 6 位股票代码或中文名称搜索
            </div>
          )}
        </div>

        {/* 关闭按钮 */}
        <button className="searchClose" onClick={onClose} aria-label="关闭搜索">
          <X size={18} />
        </button>
      </div>
    </div>
  );
}
