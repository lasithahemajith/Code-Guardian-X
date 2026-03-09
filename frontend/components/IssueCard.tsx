import React from 'react';
import SeverityBadge from './SeverityBadge';
import { ReviewIssue } from '../lib/api';

interface IssueCardProps {
  issue: ReviewIssue;
}

export default function IssueCard({ issue }: IssueCardProps) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-3 flex-wrap">
        <SeverityBadge severity={issue.severity} />
        {issue.type && (
          <span className="text-xs text-slate-400 uppercase font-medium">{issue.type}</span>
        )}
        {issue.file && (
          <code className="text-xs bg-slate-700 px-2 py-0.5 rounded text-sky-300">
            {issue.file}{issue.line ? `:${issue.line}` : ''}
          </code>
        )}
      </div>
      <p className="text-slate-200 text-sm">{issue.message}</p>
      {issue.suggestion && (
        <p className="text-slate-400 text-xs italic">
          💡 {issue.suggestion}
        </p>
      )}
    </div>
  );
}
