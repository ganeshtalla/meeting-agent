/**
 * Meeting Agent - useFileUpload Hook
 * ===================================
 *
 * Custom React hook for handling file uploads with progress tracking.
 * Integrates with TanStack Query for mutation handling.
 *
 * Packages Used:
 *   - react: Core React library
 *     - useState: Local state for progress tracking
 *     - useCallback: Memoized upload function
 *   - @tanstack/react-query: Server state management
 *     - useMutation: Handles the upload mutation
 *     - useQueryClient: Access to query cache for invalidation
 *
 * Key Features:
 *   - Upload progress tracking (0-100%)
 *   - Automatic query invalidation on success
 *   - Error handling with typed errors
 *   - Loading state management
 *
 * Usage:
 *   const { upload, isUploading, progress, error, reset } = useFileUpload();
 *
 *   const handleFileSelect = (file: File) => {
 *     upload(file, {
 *       onSuccess: (recording) => console.log('Uploaded:', recording.id),
 *       onError: (error) => console.error('Failed:', error),
 *     });
 *   };
 */

import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadRecording } from '../services/api';
import type { Recording } from '../types';

// -----------------------------------------------------------------------------
// Type Definitions
// -----------------------------------------------------------------------------

/**
 * Options for the upload function.
 */
interface UploadOptions {
  /** Callback on successful upload */
  onSuccess?: (recording: Recording) => void;
  /** Callback on upload error */
  onError?: (error: Error) => void;
}

/**
 * Return type of the useFileUpload hook.
 */
interface UseFileUploadReturn {
  /** Function to start upload */
  upload: (file: File, options?: UploadOptions) => void;
  /** Whether upload is in progress */
  isUploading: boolean;
  /** Upload progress (0-100) */
  progress: number;
  /** Error from failed upload */
  error: Error | null;
  /** The uploaded recording (after success) */
  data: Recording | null;
  /** Reset the hook state */
  reset: () => void;
}

// -----------------------------------------------------------------------------
// useFileUpload Hook
// -----------------------------------------------------------------------------

/**
 * Custom hook for handling file uploads.
 *
 * Provides:
 * - upload(): Function to upload a file
 * - isUploading: Boolean indicating upload in progress
 * - progress: Upload progress percentage (0-100)
 * - error: Error object if upload failed
 * - data: The uploaded recording on success
 * - reset(): Reset hook state for new upload
 *
 * @returns UseFileUploadReturn object with upload functionality
 *
 * @example
 * function UploadButton() {
 *   const { upload, isUploading, progress, error } = useFileUpload();
 *
 *   const handleUpload = (file: File) => {
 *     upload(file, {
 *       onSuccess: (recording) => {
 *         console.log('Uploaded successfully:', recording.id);
 *       },
 *     });
 *   };
 *
 *   return (
 *     <FileUpload
 *       onUpload={handleUpload}
 *       uploading={isUploading}
 *       progress={progress}
 *     />
 *   );
 * }
 */
export function useFileUpload(): UseFileUploadReturn {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  // Track upload progress locally (not part of mutation state)
  const [progress, setProgress] = useState(0);

  // Access query client for cache invalidation
  const queryClient = useQueryClient();

  // ---------------------------------------------------------------------------
  // Upload Mutation
  // ---------------------------------------------------------------------------
  // useMutation handles the async upload operation
  const mutation = useMutation({
    // The mutation function - calls the API
    mutationFn: async (file: File) => {
      // Reset progress at start
      setProgress(0);

      // Upload with progress callback
      return uploadRecording(file, (uploadProgress) => {
        setProgress(uploadProgress);
      });
    },

    // On success, invalidate recordings query to refresh list
    onSuccess: () => {
      // Invalidate any queries with 'recordings' in their key
      // This causes the recordings list to refetch
      queryClient.invalidateQueries({ queryKey: ['recordings'] });
    },

    // Reset progress on error
    onError: () => {
      setProgress(0);
    },
  });

  // ---------------------------------------------------------------------------
  // Upload Function
  // ---------------------------------------------------------------------------
  /**
   * Start uploading a file.
   *
   * @param file - The file to upload
   * @param options - Optional callbacks for success/error
   */
  const upload = useCallback(
    (file: File, options?: UploadOptions) => {
      mutation.mutate(file, {
        onSuccess: (recording) => {
          setProgress(100);
          options?.onSuccess?.(recording);
        },
        onError: (error) => {
          options?.onError?.(error as Error);
        },
      });
    },
    [mutation]
  );

  // ---------------------------------------------------------------------------
  // Reset Function
  // ---------------------------------------------------------------------------
  /**
   * Reset the hook state for a new upload.
   */
  const reset = useCallback(() => {
    setProgress(0);
    mutation.reset();
  }, [mutation]);

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------
  return {
    upload,
    isUploading: mutation.isPending,
    progress,
    error: mutation.error as Error | null,
    data: mutation.data ?? null,
    reset,
  };
}

export default useFileUpload;
