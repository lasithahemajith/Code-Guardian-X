import React from 'react';
import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🛡️</span>
        <span className="text-white font-bold text-xl">CodeGuardian</span>
      </div>
      <div className="flex items-center gap-6">
        <Link href="/" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">
          Dashboard
        </Link>
        <Link href="/repositories" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">
          Repositories
        </Link>
      </div>
    </nav>
  );
}
