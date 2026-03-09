import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import MetricsChart from '../components/MetricsChart';
import SeverityBadge from '../components/SeverityBadge';
import { getAlerts, ReviewIssue } from '../lib/api';

interface SummaryCard {
  label: string;
  value: string | number;
  icon: string;
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<ReviewIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAlerts()
      .then(setAlerts)
      .catch(() => setError('Could not load alerts. Make sure the API is running.'))
      .finally(() => setLoading(false));
  }, []);

  const summary: Record<string, number> = {};
  for (const alert of alerts) {
    summary[alert.severity] = (summary[alert.severity] || 0) + 1;
  }

  const cards: SummaryCard[] = [
    { label: 'Total Alerts', value: alerts.length, icon: '🔍' },
    { label: 'Critical', value: summary['critical'] || 0, icon: '🚨' },
    { label: 'High', value: summary['high'] || 0, icon: '⚠️' },
    { label: 'Medium', value: summary['medium'] || 0, icon: '📋' },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time AI code review overview</p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {cards.map((card) => (
            <div key={card.label} className="bg-slate-800 border border-slate-700 rounded-xl p-5">
              <div className="text-3xl mb-2">{card.icon}</div>
              <div className="text-2xl font-bold text-white">{card.value}</div>
              <div className="text-slate-400 text-sm mt-1">{card.label}</div>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Issues by Severity</h2>
          <MetricsChart summary={summary} />
        </div>

        {/* Recent alerts */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Alerts</h2>
          {loading && <div className="text-slate-400">Loading...</div>}
          {error && <div className="text-red-400">{error}</div>}
          {!loading && !error && alerts.length === 0 && (
            <div className="text-slate-500">No alerts yet. Connect a repository to get started.</div>
          )}
          <div className="space-y-3">
            {alerts.slice(0, 10).map((alert, idx) => (
              <div key={idx} className="flex items-start gap-3 border-b border-slate-700 pb-3 last:border-0">
                <SeverityBadge severity={alert.severity} />
                <div>
                  <span className="text-slate-200 text-sm">{alert.message}</span>
                  {alert.file && (
                    <code className="ml-2 text-xs text-sky-400">{alert.file}</code>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
