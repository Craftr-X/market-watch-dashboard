/**
 * WatchlistButton — 收藏/取消收藏按钮
 */

import { Star } from "lucide-react";
import { useWatchlistStore } from "@/store/watchlist";

interface WatchlistButtonProps {
  code: string;
  name: string;
}

export default function WatchlistButton({ code, name }: WatchlistButtonProps) {
  const { has, add, remove } = useWatchlistStore();
  const isWatched = has(code);

  function toggle() {
    if (isWatched) {
      remove(code);
    } else {
      add(code, name);
    }
  }

  return (
    <button
      className={`watchlistBtn${isWatched ? " watched" : ""}`}
      onClick={toggle}
      title={isWatched ? "取消收藏" : "加入自选"}
    >
      <Star size={16} />
      <span>{isWatched ? "已收藏" : "收藏"}</span>
    </button>
  );
}
