/**
 * Meeting Agent - API Client Service
 * ===================================
 *
 * This module provides the API client for communicating with the backend.
 * Uses Axios for HTTP requests with configured defaults.
 *
 * Packages Used:
 *   - axios: Promise-based HTTP client
 *     - axios.create(): Create configured instance
 *     - AxiosInstance: Type for axios instance
 *
 * Key Components:
 *   - api: Configured Axios instance (default export)
 *   - healthCheck(): Fetch API health status
 *   - getRecordings(): Fetch list of recordings
 *   - getRecording(): Fetch single recording by ID
 *   - uploadRecording(): Upload a new recording file
 *   - deleteRecording(): Delete a recording
 *
 * Configuration:
 *   - Base URL: http://localhost:8000/api
 *   - Default headers: Content-Type: application/json
 *
 * Usage:
 *   import api, { healthCheck, uploadRecording } from './services/api';
 *
 *   // Use named exports
 *   const health = await healthCheck();
 *
 *   // Use axios instance directly
 *   const response = await api.get('/custom-endpoint');
 */

import axios from 'axios';
import type { HealthResponse, Recording, RecordingList } from '../types';

// -----------------------------------------------------------------------------
// Axios Instance Configuration
// -----------------------------------------------------------------------------

/**
 * Configured Axios instance for API requests.
 *
 * Configuration:
 * - baseURL: Points to the backend API
 * - headers: Sets default Content-Type for JSON
 *
 * The instance can be used directly for custom requests
 * or through the exported helper functions.
 */
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// -----------------------------------------------------------------------------
// Health Check
// -----------------------------------------------------------------------------

/**
 * Fetch the API health status.
 *
 * Checks if the API is running and can connect to the database.
 *
 * @returns Promise resolving to HealthResponse
 * @throws AxiosError if request fails
 *
 * @example
 * const health = await healthCheck();
 * console.log(health.status); // 'ok'
 * console.log(health.database); // 'ok'
 */
export const healthCheck = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

// -----------------------------------------------------------------------------
// Recording Operations
// -----------------------------------------------------------------------------

/**
 * Fetch all recordings with optional filtering.
 *
 * @param skip - Number of records to skip (for pagination)
 * @param limit - Maximum number of records to return
 * @param status - Optional filter by status
 * @returns Promise resolving to RecordingList
 *
 * @example
 * const { recordings, total } = await getRecordings();
 * console.log(`Found ${total} recordings`);
 */
export const getRecordings = async (
  skip = 0,
  limit = 100,
  status?: string
): Promise<RecordingList> => {
  const params = new URLSearchParams();
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());
  if (status) {
    params.append('status_filter', status);
  }

  const response = await api.get<RecordingList>(`/recordings?${params}`);
  return response.data;
};

/**
 * Fetch a single recording by ID.
 *
 * @param id - The recording ID
 * @returns Promise resolving to Recording
 * @throws AxiosError with 404 if not found
 *
 * @example
 * const recording = await getRecording(1);
 * console.log(recording.title);
 */
export const getRecording = async (id: number): Promise<Recording> => {
  const response = await api.get<Recording>(`/recordings/${id}`);
  return response.data;
};

/**
 * Upload a new recording file.
 *
 * Uploads a file using multipart/form-data and tracks progress.
 *
 * @param file - The file to upload
 * @param onProgress - Optional callback for progress updates (0-100)
 * @returns Promise resolving to the created Recording
 * @throws AxiosError if upload fails
 *
 * @example
 * const recording = await uploadRecording(file, (progress) => {
 *   console.log(`Upload: ${progress}%`);
 * });
 * console.log(`Uploaded: ${recording.id}`);
 */
export const uploadRecording = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<Recording> => {
  // Create FormData for multipart upload
  const formData = new FormData();
  formData.append('file', file);

  // Make POST request with progress tracking
  const response = await api.post<Recording>('/recordings/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    // Track upload progress
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(progress);
      }
    },
  });

  return response.data;
};

/**
 * Delete a recording.
 *
 * Permanently deletes the recording and its associated file.
 *
 * @param id - The recording ID to delete
 * @throws AxiosError with 404 if not found
 *
 * @example
 * await deleteRecording(1);
 * console.log('Recording deleted');
 */
export const deleteRecording = async (id: number): Promise<void> => {
  await api.delete(`/recordings/${id}`);
};

// -----------------------------------------------------------------------------
// Export Default Instance
// -----------------------------------------------------------------------------

export default api;
