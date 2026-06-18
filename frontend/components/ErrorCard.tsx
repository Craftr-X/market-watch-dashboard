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

export default function ErrorCard({ message, code, onRetry }: ErrorCardProps) {
  return (
    <div className="errorCard">
      <AlertTriangle size={40} className="errorIcon" />
      <h3 className="errorTitle">
        {code ? `股票 ${code} 未找到` : "加载失败"}
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
