/**
 * Meeting Agent - App Component Tests
 * ====================================
 *
 * Tests for the root App component including:
 * - Basic rendering
 * - Section visibility
 * - Provider setup
 *
 * Packages Used:
 *   - vitest: Test framework
 *   - @testing-library/react: React testing utilities
 *
 * Running These Tests:
 *   npm test -- tests/components/App.test.tsx
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../../src/App';

// -----------------------------------------------------------------------------
// Mock API Module
// -----------------------------------------------------------------------------
// Mock the api module to prevent actual API calls during tests
vi.mock('../../src/services/api', () => ({
  healthCheck: vi.fn().mockResolvedValue({ status: 'ok', database: 'ok' }),
  uploadRecording: vi.fn().mockResolvedValue({
    id: 1,
    title: 'Test',
    status: 'pending',
  }),
  default: {
    get: vi.fn(),
    post: vi.fn(),
    defaults: { baseURL: 'http://localhost:8000/api' },
  },
}));

// -----------------------------------------------------------------------------
// App Component Tests
// -----------------------------------------------------------------------------

describe('App Component', () => {
  describe('Rendering', () => {
    it('should render the main heading', () => {
      render(<App />);
      expect(screen.getByText('Meeting Agent')).toBeInTheDocument();
    });

    it('should render the app description', () => {
      render(<App />);
      expect(
        screen.getByText(/upload meeting recordings for transcription/i)
      ).toBeInTheDocument();
    });
  });

  describe('Sections', () => {
    it('should render upload section', () => {
      render(<App />);
      expect(screen.getByText('Upload Recording')).toBeInTheDocument();
    });

    it('should render recordings section', () => {
      render(<App />);
      expect(screen.getByText('Recent Recordings')).toBeInTheDocument();
    });

    it('should render file upload dropzone', () => {
      render(<App />);
      // Check for the file input in FileUpload component
      const fileInput = screen.getByTestId('file-input');
      expect(fileInput).toBeInTheDocument();
    });
  });

  describe('Health Status', () => {
    it('should show health status in footer', async () => {
      render(<App />);
      // The mock resolves immediately, so we check for the ok status
      // Use findByText to wait for async render
      const status = await screen.findByText(/API:/i);
      expect(status).toBeInTheDocument();
    });
  });
});
