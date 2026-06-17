/**
 * 自选股 Zustand Store（localStorage 持久化）
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface WatchlistItem {
  code: string;
  name: string;
  addedAt: string;
}

interface WatchlistState {
  items: WatchlistItem[];
  add: (code: string, name: string) => void;
  remove: (code: string) => void;
  has: (code: string) => boolean;
}

export const useWatchlistStore = create<WatchlistState>()(
  persist(
    (set, get) => ({
      items: [],

      add: (code: string, name: string) => {
        if (get().has(code)) return;
        set((s) => ({
          items: [
            ...s.items,
            { code, name, addedAt: new Date().toISOString().split("T")[0] as string },
          ],
        }));
      },

      remove: (code: string) => {
        set((s) => ({ items: s.items.filter((i) => i.code !== code) }));
      },

      has: (code: string) => get().items.some((i) => i.code === code),
    }),
    {
      name: "market-watch-watchlist",
    }
  )
);
