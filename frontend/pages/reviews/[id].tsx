import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import IssueCard from '../../components/IssueCard';
import MetricsChart from '../../components/MetricsChart';
import { getReviewDetails, PRReview } from '../../lib/api';

const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'];

export default function ReviewDetails() {
  const router = useRouter();
  const { id } = router.query;
  const [review, setReview] = useState<PRReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (!id) return;
    getReviewDetails(id as string)
      .then(setReview)
      .catch(() => setError(`Review #${id} not found`))
      .finally(() => setLoading(false));
  }, [id]);

  const filteredIssues = review?.issues.filter(
    (issue) => filter === 'all' || issue.severity === filter
  ) || [];

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Review Details</h1>
          <p className="text-slate-400 mt-1">PR #{id}</p>
        </div>

        {loading && <div className="text-slate-400">Loading review...</div>}
        {error && <div className="text-red-400">{error}</div>}

        {review && (
          <>
            {/* Status */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex items-center gap-4">
              <span className="text-slate-300 text-sm">Status:</span>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${
                review.status === 'completed' ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'
              }`}>
                {review.status}
              </span>
            </div>

            {/* Summary chart */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Issue Summary</h2>
              <MetricsChart summary={review.summary} />
            </div>

            {/* Severity filter */}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  filter === 'all' ? 'bg-sky-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                All ({review.issues.length})
              </button>
              {SEVERITIES.map((sev) => {
                const count = review.issues.filter((i) => i.severity === sev).length;
                if (!count) return null;
                return (
                  <button
                    key={sev}
                    onClick={() => setFilter(sev)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors capitalize ${
                      filter === sev ? 'bg-sky-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {sev} ({count})
                  </button>
                );
              })}
            </div>

            {/* Issues list */}
            <div className="space-y-3">
              {filteredIssues.length === 0 ? (
                <div className="text-slate-500 text-center py-8">No issues with this severity.</div>
              ) : (
                filteredIssues.map((issue, idx) => <IssueCard key={idx} issue={issue} />)
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
