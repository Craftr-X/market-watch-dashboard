/**
 * WatchlistButton — 收藏/取消收藏按钮
 */

import { Star } from "lucide-react";
import { useEffect, useState } from "react";
import { useWatchlistStore } from "@/store/watchlist";

interface WatchlistButtonProps {
  code: string;
  name: string;
}

export default function WatchlistButton({ code, name }: WatchlistButtonProps) {
  // 精确订阅：只在 items 中该 code 的存在性变化时重渲染
  const isWatched = useWatchlistStore((s) => s.items.some((i) => i.code === code));
  const add = useWatchlistStore((s) => s.add);
  const remove = useWatchlistStore((s) => s.remove);

  // SSR 水合守卫：服务端渲染时始终显示未收藏态，客户端挂载后再读 localStorage
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  function toggle() {
    if (isWatched) {
      remove(code);
    } else {
      add(code, name);
    }
  }

  const showWatched = mounted && isWatched;

  return (
    <button
      className={`watchlistBtn${showWatched ? " watched" : ""}`}
      onClick={toggle}
      title={showWatched ? "取消收藏" : "加入自选"}
    >
      <Star size={16} />
      <span>{showWatched ? "已收藏" : "收藏"}</span>
    </button>
  );
}
