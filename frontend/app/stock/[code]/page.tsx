/**
 * 个股详情页 — /stock/[code]
 * 展示 K 线图 / 成交量副图 / 均线 / 统计面板 / 收藏
 */

"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Search,
  RefreshCw,
  Activity,
  Database,
} from "lucide-react";
import { useStockHistory, Period, Adjust } from "@/hooks/useStockHistory";
import { MAVariants, defaultVisibleMA } from "@/utils/ma";
import { useWatchlistStore } from "@/store/watchlist";

import KlineChart from "@/components/KlineChart";
import VolumeChart from "@/components/VolumeChart";
import StockHeader from "@/components/StockHeader";
import StockToolbar from "@/components/StockToolbar";
import StatsPanel from "@/components/StatsPanel";
import SearchModal from "@/components/SearchModal";
import WatchlistButton from "@/components/WatchlistButton";
import ErrorCard from "@/components/ErrorCard";

const API_BASE =
  (typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000"
    : "http://127.0.0.1:8000");

function StockPageContent({ code }: { code: string }) {
  const searchParams = useSearchParams();
  const initialPeriod = (searchParams.get("period") as Period) ?? "daily";
  const initialAdjust = (searchParams.get("adjust") as Adjust) ?? "qfq";

  const [period, setPeriod] = useState<Period>(initialPeriod);
  const [adjust, setAdjust] = useState<Adjust>(initialAdjust);
  const [showMA, setShowMA] = useState<Record<keyof MAVariants, boolean>>(
    defaultVisibleMA(initialPeriod)
  );
  const [showSearch, setShowSearch] = useState(false);

  const { data, source, loading, error, refetch } = useStockHistory(
    code,
    period,
    adjust
  );

  // 周期切换时同步更新默认均线配置
  function handlePeriodChange(p: Period) {
    setPeriod(p);
    setShowMA(defaultVisibleMA(p));
  }

  function handleMAChange(key: keyof MAVariants, visible: boolean) {
    setShowMA((prev) => ({ ...prev, [key]: visible }));
  }

  return (
    <main className="stockPage">
      {/* ================================================================
          顶部导航栏
      ================================================================ */}
      <header className="stockNav">
        <div className="navLeft">
          <Link href="/" className="navBack">
            <ArrowLeft size={16} />
            返回首页
          </Link>
        </div>

        <div className="navCenter">
          <span className="navBrand">A股历史走势</span>
        </div>

        <div className="navRight">
          <div className="metaPill">
            <Database size={13} />
            <span>{data?.meta.total_count ? "akshare" : "loading"}</span>
          </div>
          {data?.meta && (
            <div className="metaPill">
              <Activity size={13} />
              <span>{data.meta.total_count} 根</span>
            </div>
          )}
          <button
            className="navIconBtn"
            onClick={() => setShowSearch(true)}
            title="搜索股票"
            aria-label="打开搜索"
          >
            <Search size={17} />
          </button>
          <button
            className="navIconBtn"
            onClick={refetch}
            disabled={loading}
            title="刷新数据"
            aria-label="刷新数据"
          >
            <RefreshCw size={17} className={loading ? "spin" : ""} />
          </button>
        </div>
      </header>

      {/* ================================================================
          风险声明
      ================================================================ */}
      <div className="notice">
        <span>本系统仅用于市场学习和行情复盘，不构成投资建议。</span>
      </div>

      {/* ================================================================
          模拟/降级数据提示
      ================================================================ */}
      {source && source !== "akshare" && (
        <div className="notice warn">
          <span>
            ⚠️ 当前展示为{source === "mock_seed" ? "模拟" : "本地降级"}数据，仅供界面预览，非真实行情
          </span>
        </div>
      )}

      {/* ================================================================
          加载中状态
      ================================================================ */}
      {loading && !data && (
        <div className="chartLoading">
          <div className="spinner large" />
          <p>正在从数据源拉取历史数据…</p>
          <small>首次查询约需 30 秒，请稍候</small>
        </div>
      )}

      {/* ================================================================
          错误状态
      ================================================================ */}
      {error && !data && <ErrorCard message={error} code={code} onRetry={refetch} />}

      {/* ================================================================
          图表内容区
      ================================================================ */}
      {data && (
        <>
          {/* 个股头部信息 */}
          <StockHeader code={data.code} name={data.name} meta={data.meta} />

          {/* 工具栏 */}
          <StockToolbar
            period={period}
            adjust={adjust}
            showMA={showMA}
            onPeriodChange={handlePeriodChange}
            onAdjustChange={setAdjust}
            onMAChange={handleMAChange}
          />

          {/* K 线主图 */}
          <div className="chartCard">
            <div className="chartTitle">
              <span>
                {period === "daily"
                  ? "日线"
                  : period === "weekly"
                  ? "周线"
                  : "月线"}
                {adjust === "qfq" ? " · 前复权" : " · 不复权"}
              </span>
              {loading && (
                <span className="chartBadge loading">数据更新中…</span>
              )}
            </div>
            <KlineChart
              candles={data.candles}
              showMA={showMA}
              height={400}
            />
          </div>

          {/* 成交量副图 */}
          <div className="chartCard volumeCard">
            <div className="chartTitle">成交量（手）</div>
            <VolumeChart candles={data.candles} height={140} />
          </div>

          {/* 统计面板 */}
          <StatsPanel candles={data.candles} />

          {/* 收藏按钮 */}
          <div className="watchlistAction">
            <WatchlistButton code={data.code} name={data.name} />
          </div>
        </>
      )}

      {/* ================================================================
          搜索弹层
      ================================================================ */}
      {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}
    </main>
  );
}

/** 包装 Suspense，确保 useSearchParams 正常工作。
 *  code 来自动态路由段 [code]（首页/搜索链接均不带 ?code=），不是 query string。 */
export default function StockPage({ params }: { params: { code: string } }) {
  return (
    <Suspense fallback={<div className="stockPageLoading">加载中…</div>}>
      <StockPageContent code={params.code} />
    </Suspense>
  );
}
