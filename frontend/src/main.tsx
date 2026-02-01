/**
 * Meeting Agent - Application Entry Point
 * ========================================
 *
 * This is the main entry point for the React application.
 * It mounts the root App component to the DOM.
 *
 * Packages Used:
 *   - react: Core React library
 *     - StrictMode: Development mode wrapper that highlights potential problems
 *   - react-dom/client: React DOM rendering for browsers
 *     - createRoot: Creates a React root for rendering
 *
 * Key Components:
 *   - createRoot(): Creates the React 18 root for concurrent features
 *   - StrictMode: Enables additional development checks
 *   - App: The root application component
 *
 * DOM Target:
 *   The app is mounted to the element with id="root" in index.html
 *
 * CSS Import:
 *   Global styles are imported here to ensure they're loaded first
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// -----------------------------------------------------------------------------
// Application Bootstrap
// -----------------------------------------------------------------------------
// createRoot is the React 18 way to initialize the application.
// It enables concurrent features like automatic batching and transitions.
//
// The non-null assertion (!) tells TypeScript that getElementById
// will definitely find the element (it exists in index.html).
ReactDOM.createRoot(document.getElementById('root')!).render(
  // StrictMode is a development tool that:
  // - Identifies components with unsafe lifecycles
  // - Warns about deprecated API usage
  // - Detects unexpected side effects (by double-invoking certain functions)
  // - Ensures reusable state (for future React features)
  // Note: StrictMode only runs in development, not production
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
