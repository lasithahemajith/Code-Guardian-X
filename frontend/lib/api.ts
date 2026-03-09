import axios from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE_URL });

// Attach token from localStorage if present
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface Repository {
  id: number;
  name: string;
  provider: string;
  created_at: string;
}

export interface ReviewIssue {
  file?: string;
  line?: number;
  type?: string;
  severity: string;
  message: string;
  suggestion?: string;
}

export interface PRReview {
  pr_id: number;
  status: string;
  summary: Record<string, number>;
  issues: ReviewIssue[];
}

export async function login(username: string, password: string): Promise<string> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  const res = await api.post('/auth/login', params);
  return res.data.access_token;
}

export async function getRepositories(): Promise<Repository[]> {
  const res = await api.get('/repositories');
  return res.data;
}

export async function connectRepository(data: { name: string; provider: string }): Promise<Repository> {
  const res = await api.post('/repositories/connect', data);
  return res.data;
}

export async function getReviewDetails(prId: string): Promise<PRReview> {
  const res = await api.get(`/reviews/${prId}`);
  return res.data;
}

export async function getAlerts(): Promise<ReviewIssue[]> {
  const res = await api.get('/alerts');
  return res.data;
}

export default api;
