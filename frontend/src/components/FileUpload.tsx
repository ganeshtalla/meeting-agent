/**
 * Meeting Agent - File Upload Component
 * ======================================
 *
 * A drag-and-drop file upload component for audio/video recordings.
 * Supports both drag-drop and click-to-select interactions.
 *
 * Packages Used:
 *   - react: Core React library
 *     - useState: Local state management
 *     - useRef: DOM element references
 *     - useCallback: Memoized callbacks
 *     - DragEvent, ChangeEvent: Event type definitions
 *
 * Key Components:
 *   - FileUpload: Main component with drop zone
 *   - ProgressBar: Upload progress indicator
 *   - ErrorMessage: Validation error display
 *
 * Props:
 *   - onUpload: Callback when file is selected (required)
 *   - onProgress: Callback for upload progress updates
 *   - onError: Callback for error handling
 *   - accept: Accepted MIME types (default: audio/*, video/*)
 *   - maxSizeMB: Maximum file size in MB (default: 500)
 *   - disabled: Disable upload functionality
 *
 * Usage:
 *   <FileUpload
 *     onUpload={(file) => uploadToServer(file)}
 *     onProgress={(progress) => setProgress(progress)}
 *     onError={(error) => showError(error)}
 *   />
 */

import { useState, useRef, useCallback, DragEvent, ChangeEvent } from 'react';
import './FileUpload.css';

// -----------------------------------------------------------------------------
// Type Definitions
// -----------------------------------------------------------------------------

/**
 * Props for the FileUpload component.
 */
interface FileUploadProps {
  /** Callback when a valid file is selected */
  onUpload: (file: File) => void;
  /** Callback for upload progress (0-100) */
  onProgress?: (progress: number) => void;
  /** Callback when an error occurs */
  onError?: (error: string) => void;
  /** Accepted MIME types */
  accept?: string;
  /** Maximum file size in MB */
  maxSizeMB?: number;
  /** Disable the upload component */
  disabled?: boolean;
  /** Show upload progress */
  uploading?: boolean;
  /** Current upload progress (0-100) */
  progress?: number;
}

// -----------------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------------

/** Allowed audio MIME types */
const AUDIO_TYPES = [
  'audio/wav',
  'audio/x-wav',
  'audio/wave',
  'audio/mpeg',
  'audio/mp3',
  'audio/mp4',
  'audio/x-m4a',
  'audio/aac',
  'audio/ogg',
  'audio/flac',
  'audio/webm',
];

/** Allowed video MIME types */
const VIDEO_TYPES = [
  'video/mp4',
  'video/mpeg',
  'video/webm',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
];

/** All allowed MIME types */
const ALLOWED_TYPES = [...AUDIO_TYPES, ...VIDEO_TYPES];

/** Allowed file extensions */
const ALLOWED_EXTENSIONS = [
  'wav', 'mp3', 'm4a', 'aac', 'ogg', 'flac', 'webm',
  'mp4', 'mpeg', 'mpg', 'mov', 'avi', 'mkv',
];

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

/**
 * Check if a file type is valid.
 *
 * @param file - The file to validate
 * @returns true if the file type is allowed
 */
function isValidFileType(file: File): boolean {
  // Check MIME type
  if (ALLOWED_TYPES.includes(file.type)) {
    return true;
  }

  // Fallback: check extension
  const extension = file.name.split('.').pop()?.toLowerCase();
  return extension ? ALLOWED_EXTENSIONS.includes(extension) : false;
}

/**
 * Format file size for display.
 *
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "5.2 MB")
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

// -----------------------------------------------------------------------------
// FileUpload Component
// -----------------------------------------------------------------------------

/**
 * File upload component with drag-and-drop support.
 *
 * Features:
 * - Drag and drop file upload
 * - Click to select file
 * - File type validation
 * - File size validation
 * - Upload progress display
 * - Error messages
 *
 * @param props - Component props
 * @returns JSX element
 */
export function FileUpload({
  onUpload,
  onProgress,
  onError,
  accept = 'audio/*,video/*',
  maxSizeMB = 500,
  disabled = false,
  uploading = false,
  progress = 0,
}: FileUploadProps) {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Ref for the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ---------------------------------------------------------------------------
  // File Validation
  // ---------------------------------------------------------------------------
  /**
   * Validate a file and call onUpload if valid.
   */
  const handleFile = useCallback((file: File) => {
    // Clear previous error
    setError(null);

    // Validate file type
    if (!isValidFileType(file)) {
      const errorMsg = `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
      setError(errorMsg);
      onError?.(errorMsg);
      return;
    }

    // Validate file size
    const maxBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      const errorMsg = `File too large: ${formatFileSize(file.size)}. Maximum: ${maxSizeMB}MB`;
      setError(errorMsg);
      onError?.(errorMsg);
      return;
    }

    // File is valid
    setSelectedFile(file);
    onUpload(file);
  }, [maxSizeMB, onUpload, onError]);

  // ---------------------------------------------------------------------------
  // Drag and Drop Handlers
  // ---------------------------------------------------------------------------
  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !uploading) {
      setIsDragging(true);
    }
  }, [disabled, uploading]);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled || uploading) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [disabled, uploading, handleFile]);

  // ---------------------------------------------------------------------------
  // Click Handler
  // ---------------------------------------------------------------------------
  const handleClick = useCallback(() => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click();
    }
  }, [disabled, uploading]);

  const handleFileChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  }, [handleFile]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="file-upload-container">
      {/* Drop Zone */}
      <div
        className={`file-upload-dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload file"
      >
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          disabled={disabled || uploading}
          className="file-upload-input"
          data-testid="file-input"
          aria-hidden="true"
        />

        {/* Upload Icon */}
        <div className="file-upload-icon">
          {uploading ? '⏳' : '📁'}
        </div>

        {/* Instructions */}
        {!uploading && !selectedFile && (
          <div className="file-upload-text">
            <p className="file-upload-primary">
              Drag and drop your file here
            </p>
            <p className="file-upload-secondary">
              or click to select
            </p>
            <p className="file-upload-hint">
              Supported: WAV, MP3, M4A, MP4, MOV, AVI (max {maxSizeMB}MB)
            </p>
          </div>
        )}

        {/* Selected File Info */}
        {selectedFile && !uploading && (
          <div className="file-upload-selected">
            <p className="file-upload-filename">{selectedFile.name}</p>
            <p className="file-upload-size">{formatFileSize(selectedFile.size)}</p>
          </div>
        )}

        {/* Upload Progress */}
        {uploading && (
          <div className="file-upload-progress">
            <p>Uploading...</p>
            <div
              className="progress-bar"
              role="progressbar"
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="progress-bar-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="progress-text">{progress}%</p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="file-upload-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
