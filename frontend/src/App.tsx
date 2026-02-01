/**
 * Meeting Agent - Root Application Component
 * ==========================================
 *
 * This is the root component of the Meeting Agent frontend.
 * It sets up global providers and renders the main application layout.
 *
 * Packages Used:
 *   - @tanstack/react-query: Server state management library
 *     - QueryClient: Creates and configures the query cache
 *     - QueryClientProvider: React context provider for queries
 *     - useQuery: Hook for fetching and caching data
 *
 * Key Components:
 *   - queryClient: Singleton QueryClient instance for the app
 *   - HealthStatus: Component displaying API/database health
 *   - UploadSection: File upload interface with progress
 *   - AppContent: Main application content and layout
 *   - App: Root component wrapping everything with providers
 *
 * Component Hierarchy:
 *   App
 *   └── QueryClientProvider (provides query context)
 *       └── AppContent (main layout)
 *           ├── header (title and description)
 *           ├── main
 *           │   ├── UploadSection (file upload)
 *           │   └── recordings section (placeholder)
 *           └── footer (health status)
 */

import { useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { healthCheck } from './services/api';
import { FileUpload } from './components/FileUpload';
import { useFileUpload } from './hooks/useFileUpload';
import type { HealthResponse, Recording } from './types';

// -----------------------------------------------------------------------------
// Query Client Configuration
// -----------------------------------------------------------------------------
// QueryClient manages the cache of all queries in the application.
// It's created once and provided to the entire app via context.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry failed requests up to 3 times
      retry: 3,
      // Consider data fresh for 30 seconds
      staleTime: 30000,
    },
  },
});

// -----------------------------------------------------------------------------
// Health Status Component
// -----------------------------------------------------------------------------
/**
 * Displays the current health status of the API and database.
 *
 * Uses TanStack Query to:
 * - Fetch health status on mount
 * - Auto-refetch every 30 seconds
 * - Cache the result for subsequent renders
 *
 * @returns JSX element showing health status
 */
function HealthStatus() {
  const { data, isLoading, error } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <div className="status loading">Connecting to API...</div>;
  }

  if (error) {
    return <div className="status error">API Unavailable</div>;
  }

  return (
    <div className="status ok">
      API: {data?.status} | Database: {data?.database}
    </div>
  );
}

// -----------------------------------------------------------------------------
// Upload Section Component
// -----------------------------------------------------------------------------
/**
 * Section containing the file upload interface.
 *
 * Integrates FileUpload component with useFileUpload hook for:
 * - File selection and validation
 * - Upload progress tracking
 * - Success/error notifications
 *
 * @returns JSX element with upload interface
 */
function UploadSection() {
  // Upload hook provides upload function and state
  const { upload, isUploading, progress, error, data, reset } = useFileUpload();

  // Track last uploaded recording for display
  const [lastUpload, setLastUpload] = useState<Recording | null>(null);

  /**
   * Handle file selection from FileUpload component.
   */
  const handleUpload = (file: File) => {
    upload(file, {
      onSuccess: (recording) => {
        setLastUpload(recording);
      },
      onError: (err) => {
        console.error('Upload failed:', err);
      },
    });
  };

  /**
   * Handle uploading another file.
   */
  const handleUploadAnother = () => {
    setLastUpload(null);
    reset();
  };

  return (
    <section className="upload-section">
      <h2>Upload Recording</h2>
      <p>Drag and drop or click to upload audio/video files</p>

      {/* Show success message if upload completed */}
      {lastUpload && !isUploading && (
        <div className="upload-success">
          <div className="success-icon">✓</div>
          <div className="success-content">
            <p className="success-title">Upload successful!</p>
            <p className="success-details">
              <strong>{lastUpload.title}</strong> ({lastUpload.original_filename})
            </p>
            <p className="success-status">
              Status: <span className="status-badge pending">{lastUpload.status}</span>
            </p>
            <button
              className="upload-another-btn"
              onClick={handleUploadAnother}
            >
              Upload Another
            </button>
          </div>
        </div>
      )}

      {/* Show upload interface if no recent upload */}
      {!lastUpload && (
        <FileUpload
          onUpload={handleUpload}
          uploading={isUploading}
          progress={progress}
          onError={(err) => console.error('Validation error:', err)}
        />
      )}

      {/* Show error if upload failed */}
      {error && !isUploading && (
        <div className="upload-error-message">
          <p>Upload failed: {error.message}</p>
          <button onClick={reset}>Try Again</button>
        </div>
      )}
    </section>
  );
}

// -----------------------------------------------------------------------------
// App Content Component
// -----------------------------------------------------------------------------
/**
 * Main application content and layout.
 *
 * @returns JSX element containing the app layout
 */
function AppContent() {
  return (
    <div className="app">
      {/* Header */}
      <header>
        <h1>Meeting Agent</h1>
        <p>Upload meeting recordings for transcription and analysis</p>
      </header>

      {/* Main Content */}
      <main>
        {/* Upload Section */}
        <UploadSection />

        {/* Recordings List - Phase 6 */}
        <section className="recordings-section">
          <h2>Recent Recordings</h2>
          <div className="recordings-placeholder">
            Recordings list will be added in Phase 6
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer>
        <HealthStatus />
      </footer>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Root App Component
// -----------------------------------------------------------------------------
/**
 * Root application component that sets up providers.
 *
 * @returns JSX element with providers wrapping AppContent
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
