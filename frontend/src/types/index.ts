/**
 * Meeting Agent - TypeScript Type Definitions
 * ============================================
 *
 * This file contains all TypeScript interfaces and types used throughout
 * the frontend application. Types mirror the backend API schemas.
 *
 * Organization:
 *   1. Recording Types - Meeting recording data structures
 *   2. Analysis Types - Transcription and analysis results
 *   3. API Response Types - Common API response formats
 *
 * Usage:
 *   import type { Recording, HealthResponse } from '../types';
 *
 *   const recording: Recording = await api.get('/recordings/1');
 */

// =============================================================================
// Recording Types
// =============================================================================

/**
 * Status of a recording in the processing pipeline.
 *
 * - pending: Uploaded, waiting to be processed
 * - processing: Currently being transcribed/analyzed
 * - completed: Successfully processed
 * - failed: Processing failed (check error_message)
 */
export type RecordingStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * A meeting recording with metadata and processing status.
 *
 * This interface matches the RecordingResponse schema from the backend.
 */
export interface Recording {
  /** Unique identifier (database primary key) */
  id: number;

  /** Title of the recording (user-provided or derived from filename) */
  title: string;

  /** Original filename as uploaded */
  original_filename: string;

  /** Path to the stored file on the server */
  file_path: string;

  /** File size in bytes */
  file_size: number;

  /** MIME type (e.g., 'audio/wav', 'video/mp4') */
  mime_type: string;

  /** Duration of the recording in seconds (null if not yet processed) */
  duration_seconds: number | null;

  /** Current processing status */
  status: RecordingStatus;

  /** Error message if status is 'failed' */
  error_message: string | null;

  /** ISO timestamp when the recording was uploaded */
  created_at: string;

  /** ISO timestamp when the record was last modified */
  updated_at: string | null;

  /** ISO timestamp when processing completed */
  processed_at: string | null;
}

/**
 * Response for listing multiple recordings.
 */
export interface RecordingList {
  /** Array of recording objects */
  recordings: Recording[];

  /** Total count of recordings (for pagination) */
  total: number;
}

// =============================================================================
// Analysis Types
// =============================================================================

/**
 * An action item extracted from the meeting.
 */
export interface ActionItem {
  /** Speaker who was assigned the action */
  speaker: string;

  /** Description of the task */
  task: string;

  /** Optional due date */
  due_date?: string;
}

/**
 * Analysis results from the LLM.
 */
export interface Analysis {
  /** Summary of the meeting */
  summary: string;

  /** List of action items with speaker attribution */
  action_items: ActionItem[];

  /** Key decisions made during the meeting */
  decisions: string[];
}

/**
 * A segment of the transcript with timing information.
 */
export interface TranscriptSegment {
  /** Start time in seconds */
  start: number;

  /** End time in seconds */
  end: number;

  /** Transcribed text for this segment */
  text: string;

  /** Optional speaker identification */
  speaker?: string;
}

/**
 * Full transcript of a recording.
 */
export interface Transcript {
  /** Array of transcript segments with timing */
  segments: TranscriptSegment[];

  /** Full transcript text (concatenated segments) */
  full_text: string;
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Health check response from the API.
 */
export interface HealthResponse {
  /** API status ('ok') */
  status: string;

  /** Database connection status ('ok' or 'error') */
  database: string;
}

/**
 * Error response from the API.
 */
export interface ApiError {
  /** Error message */
  detail: string;

  /** Optional error code */
  code?: string;
}

/**
 * Paginated response wrapper.
 */
export interface PaginatedResponse<T> {
  /** Array of items */
  items: T[];

  /** Total count of items */
  total: number;

  /** Current page number */
  page: number;

  /** Items per page */
  per_page: number;
}
