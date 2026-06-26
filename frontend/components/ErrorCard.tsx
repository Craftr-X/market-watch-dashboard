/**
 * ErrorCard — 统一错误状态卡片
 */

import { AlertTriangle, RefreshCw } from "lucide-react";
import Link from "next/link";

interface ErrorCardProps {
  message: string;
  code?: string;
  onRetry?: () => void;
}

/** 根据错误信息推断标题，避免网络错误也显示"股票 X 未找到" */
function inferTitle(message: string, code?: string): string {
  if (message.includes("未找到") || message.includes("不存在") || message.includes("退市")) {
    return code ? `股票 ${code} 未找到` : "未找到股票";
  }
  if (message.includes("超时") || message.includes("timeout")) return "数据获取超时";
  if (message.includes("网络") || message.includes("后端")) return "网络连接失败";
  if (message.includes("频繁") || message.includes("429")) return "请求过于频繁";
  return "加载失败";
}

export default function ErrorCard({ message, code, onRetry }: ErrorCardProps) {
  return (
    <div className="errorCard">
      <AlertTriangle size={40} className="errorIcon" />
      <h3 className="errorTitle">
        {inferTitle(message, code)}
      </h3>
      <p className="errorMessage">{message}</p>
      <div className="errorActions">
        {onRetry && (
          <button className="errorRetry" onClick={onRetry}>
            <RefreshCw size={15} />
            重新加载
          </button>
        )}
        <Link href="/" className="errorBack">
          返回首页
        </Link>
      </div>
    </div>
  );
}
