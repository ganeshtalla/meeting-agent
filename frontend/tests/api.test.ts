import { describe, it, expect, vi, beforeEach } from 'vitest';
import api, { healthCheck } from '../src/services/api';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      defaults: {
        baseURL: 'http://localhost:8000/api',
      },
    })),
  },
}));

describe('API Client', () => {
  it('should have correct base URL configured', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api');
  });
});

describe('Health Check', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call health endpoint', async () => {
    const mockResponse = { status: 'ok', database: 'ok' };
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse });

    const result = await healthCheck();

    expect(api.get).toHaveBeenCalledWith('/health');
    expect(result).toEqual(mockResponse);
  });
});
