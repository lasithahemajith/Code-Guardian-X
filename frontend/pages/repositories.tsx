import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getRepositories, connectRepository, Repository } from '../lib/api';

export default function Repositories() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', provider: 'github' });
  const [error, setError] = useState('');

  useEffect(() => {
    getRepositories()
      .then(setRepos)
      .catch(() => setError('Failed to load repositories'))
      .finally(() => setLoading(false));
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const repo = await connectRepository(form);
      setRepos((prev) => [...prev, repo]);
      setShowForm(false);
      setForm({ name: '', provider: 'github' });
    } catch {
      setError('Failed to connect repository. Ensure you are logged in.');
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Repositories</h1>
            <p className="text-slate-400 mt-1">Manage connected repositories</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + Connect Repository
          </button>
        </div>

        {error && <div className="text-red-400 text-sm">{error}</div>}

        {showForm && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Connect New Repository</h2>
            <form onSubmit={handleConnect} className="space-y-4">
              <div>
                <label className="text-slate-300 text-sm block mb-1">Repository name (owner/repo)</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="company/backend"
                  required
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="text-slate-300 text-sm block mb-1">Provider</label>
                <select
                  value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-sky-500"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                  <option value="bitbucket">Bitbucket</option>
                </select>
              </div>
              <button
                type="submit"
                className="bg-sky-600 hover:bg-sky-500 text-white px-6 py-2 rounded-lg text-sm font-medium"
              >
                Connect
              </button>
            </form>
          </div>
        )}

        {loading ? (
          <div className="text-slate-400">Loading repositories...</div>
        ) : repos.length === 0 ? (
          <div className="bg-slate-800 border border-dashed border-slate-600 rounded-xl p-12 text-center">
            <div className="text-4xl mb-3">📦</div>
            <p className="text-slate-400">No repositories connected yet.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {repos.map((repo) => (
              <div key={repo.id} className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex items-center justify-between">
                <div>
                  <h3 className="text-white font-semibold">{repo.name}</h3>
                  <span className="text-slate-400 text-sm capitalize">{repo.provider}</span>
                </div>
                <span className="text-slate-500 text-xs">{new Date(repo.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
