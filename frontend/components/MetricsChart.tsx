import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#64748b',
};

interface MetricsChartProps {
  summary: Record<string, number>;
}

export default function MetricsChart({ summary }: MetricsChartProps) {
  const data = Object.entries(summary)
    .filter(([, count]) => count > 0)
    .map(([severity, count]) => ({ severity, count }));

  if (data.length === 0) {
    return <div className="text-slate-500 text-sm text-center py-8">No issues detected</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <XAxis dataKey="severity" tick={{ fill: '#94a3b8', fontSize: 12 }} />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
          labelStyle={{ color: '#e2e8f0' }}
          itemStyle={{ color: '#94a3b8' }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] || '#64748b'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
