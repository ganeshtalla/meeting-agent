/**
 * Meeting Agent - FileUpload Component Tests
 * ==========================================
 *
 * Tests for the FileUpload component functionality including:
 * - Rendering drop zone
 * - File selection behavior
 * - Drag and drop behavior
 * - Upload progress display
 *
 * Packages Used:
 *   - vitest: Test framework
 *   - @testing-library/react: React testing utilities
 *   - @testing-library/user-event: User interaction simulation
 *
 * Running These Tests:
 *   npm test -- tests/components/FileUpload.test.tsx
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileUpload } from '../../src/components/FileUpload';

// -----------------------------------------------------------------------------
// Render Tests
// -----------------------------------------------------------------------------

describe('FileUpload Component', () => {
  describe('Rendering', () => {
    it('should render drop zone', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      // Check for drag and drop text
      expect(screen.getByText(/drag and drop your file here/i)).toBeInTheDocument();
    });

    it('should render file input', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      // Check for hidden file input
      const input = screen.getByTestId('file-input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'file');
    });

    it('should show supported file types hint', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      expect(screen.getByText(/wav, mp3/i)).toBeInTheDocument();
    });

    it('should show max file size in hint', () => {
      render(<FileUpload onUpload={vi.fn()} maxSizeMB={100} />);

      expect(screen.getByText(/max 100mb/i)).toBeInTheDocument();
    });

    it('should render click to select text', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      expect(screen.getByText(/or click to select/i)).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Drag and Drop Tests
  // ---------------------------------------------------------------------------

  describe('Drag and Drop', () => {
    it('should show dragging state when file is dragged over', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });

      fireEvent.dragEnter(dropzone);

      expect(dropzone).toHaveClass('dragging');
    });

    it('should remove dragging state when file leaves', () => {
      render(<FileUpload onUpload={vi.fn()} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });

      fireEvent.dragEnter(dropzone);
      fireEvent.dragLeave(dropzone);

      expect(dropzone).not.toHaveClass('dragging');
    });

    it('should accept dropped audio files', () => {
      const onUpload = vi.fn();
      render(<FileUpload onUpload={onUpload} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      const file = new File(['audio content'], 'test.mp3', {
        type: 'audio/mpeg',
      });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      expect(onUpload).toHaveBeenCalledWith(file);
    });

    it('should accept dropped video files', () => {
      const onUpload = vi.fn();
      render(<FileUpload onUpload={onUpload} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      const file = new File(['video content'], 'test.mp4', {
        type: 'video/mp4',
      });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      expect(onUpload).toHaveBeenCalledWith(file);
    });

    it('should reject dropped non-audio/video files', () => {
      const onUpload = vi.fn();
      const onError = vi.fn();
      render(<FileUpload onUpload={onUpload} onError={onError} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      const file = new File(['text content'], 'test.txt', {
        type: 'text/plain',
      });

      fireEvent.drop(dropzone, {
        dataTransfer: {
          files: [file],
        },
      });

      // Should not call onUpload
      expect(onUpload).not.toHaveBeenCalled();
      // Should call onError
      expect(onError).toHaveBeenCalled();
      // Should show error message
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Upload Progress Tests
  // ---------------------------------------------------------------------------

  describe('Upload Progress', () => {
    it('should show progress bar when uploading', () => {
      render(<FileUpload onUpload={vi.fn()} uploading={true} progress={45} />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '45');
    });

    it('should show progress percentage', () => {
      render(<FileUpload onUpload={vi.fn()} uploading={true} progress={75} />);

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should show uploading text during upload', () => {
      render(<FileUpload onUpload={vi.fn()} uploading={true} progress={50} />);

      expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    });

    it('should hide drop zone instructions when uploading', () => {
      render(<FileUpload onUpload={vi.fn()} uploading={true} progress={50} />);

      expect(screen.queryByText(/drag and drop your file here/i)).not.toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Disabled State Tests
  // ---------------------------------------------------------------------------

  describe('Disabled State', () => {
    it('should have disabled file input when disabled', () => {
      render(<FileUpload onUpload={vi.fn()} disabled={true} />);

      const input = screen.getByTestId('file-input');
      expect(input).toBeDisabled();
    });

    it('should show disabled styling', () => {
      render(<FileUpload onUpload={vi.fn()} disabled={true} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      expect(dropzone).toHaveClass('disabled');
    });

    it('should not accept dropped files when disabled', () => {
      const onUpload = vi.fn();
      render(<FileUpload onUpload={onUpload} disabled={true} />);

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' });

      fireEvent.drop(dropzone, {
        dataTransfer: { files: [file] },
      });

      expect(onUpload).not.toHaveBeenCalled();
    });
  });

  // ---------------------------------------------------------------------------
  // File Size Validation Tests
  // ---------------------------------------------------------------------------

  describe('File Size Validation', () => {
    it('should reject files that exceed size limit', () => {
      const onUpload = vi.fn();
      const onError = vi.fn();

      // Set max size to very small for testing (1 byte)
      render(
        <FileUpload
          onUpload={onUpload}
          onError={onError}
          maxSizeMB={0.000001}
        />
      );

      const dropzone = screen.getByRole('button', { name: /upload file/i });
      const file = new File(['some content here'], 'test.mp3', {
        type: 'audio/mpeg',
      });

      fireEvent.drop(dropzone, {
        dataTransfer: { files: [file] },
      });

      expect(onUpload).not.toHaveBeenCalled();
      expect(onError).toHaveBeenCalled();
      expect(screen.getByText(/file too large/i)).toBeInTheDocument();
    });
  });
});
