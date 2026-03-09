import React from 'react';
import clsx from 'clsx';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-900 text-red-200 border border-red-700',
  high: 'bg-orange-900 text-orange-200 border border-orange-700',
  medium: 'bg-yellow-900 text-yellow-200 border border-yellow-700',
  low: 'bg-blue-900 text-blue-200 border border-blue-700',
  info: 'bg-slate-700 text-slate-300 border border-slate-600',
};

interface SeverityBadgeProps {
  severity: string;
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const style = SEVERITY_STYLES[severity.toLowerCase()] || SEVERITY_STYLES.info;
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase', style)}>
      {severity}
    </span>
  );
}
