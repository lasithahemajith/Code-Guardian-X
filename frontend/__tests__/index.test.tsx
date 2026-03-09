import React from 'react';

// Mock ResizeObserver (not available in jsdom)
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({ query: {} }),
}));

// Mock API calls
jest.mock('../lib/api', () => ({
  getAlerts: jest.fn().mockResolvedValue([
    { severity: 'critical', message: 'SQL injection detected', file: 'auth.py', line: 5 },
    { severity: 'high', message: 'Hardcoded secret', file: 'config.py' },
  ]),
}));

import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../pages/index';

describe('Dashboard', () => {
  it('renders title', () => {
    render(<Dashboard />);
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeTruthy();
  });

  it('renders summary cards', () => {
    render(<Dashboard />);
    expect(screen.getByText('Total Alerts')).toBeTruthy();
    expect(screen.getByText('Critical')).toBeTruthy();
  });

  it('shows alerts after loading', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('SQL injection detected')).toBeTruthy();
    });
  });
});
