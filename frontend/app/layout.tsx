import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "A股每日行情与强势观察",
  description: "个人市场学习与复盘工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
