# Meeting Agent - Frontend

## Overview

This is the React frontend for the Meeting Agent application. It provides a user interface for uploading meeting recordings and viewing transcription/analysis results.

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18 | UI component library |
| Language | TypeScript | Type-safe JavaScript |
| Build Tool | Vite | Fast development and bundling |
| State Management | TanStack Query | Server state management |
| HTTP Client | Axios | API requests |
| Testing | Vitest | Unit and integration testing |
| Test Utils | Testing Library | Component testing utilities |

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Application entry point
│   ├── App.tsx               # Root component
│   ├── index.css             # Global styles
│   ├── vite-env.d.ts         # Vite type declarations
│   ├── components/           # React components (Phase 2+)
│   │   ├── FileUpload.tsx
│   │   ├── RecordingList.tsx
│   │   ├── ProcessingStatus.tsx
│   │   └── ResultsView.tsx
│   ├── hooks/                # Custom React hooks (Phase 2+)
│   │   └── useRecordings.ts
│   ├── services/             # API client and utilities
│   │   └── api.ts
│   ├── types/                # TypeScript type definitions
│   │   └── index.ts
│   └── test/                 # Test setup
│       └── setup.ts
├── tests/                    # Test files
│   ├── api.test.ts
│   └── components/
│       └── App.test.tsx
├── public/                   # Static assets
│   └── vite.svg
├── index.html                # HTML template
├── package.json              # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── tsconfig.node.json        # TypeScript config for Node
└── vite.config.ts            # Vite configuration
```

## Installation

```bash
# Install dependencies
npm install

# Or using yarn
yarn install
```

## Running the Application

```bash
# Development server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Running Tests

```bash
# Run tests in watch mode
npm test

# Run tests once
npm test -- --run

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server on port 5173 |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm test` | Run tests with Vitest |
| `npm run test:ui` | Run tests with UI |
| `npm run test:coverage` | Run tests with coverage report |

## Environment Configuration

The frontend uses Vite's built-in environment variable support:

```env
# .env.local (create this file)
VITE_API_URL=http://localhost:8000/api
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

## API Proxy

In development, Vite proxies API requests to avoid CORS issues:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## Phase 1 Implementation

Phase 1 establishes the frontend foundation:

1. **React + TypeScript Setup** - Vite-based project with strict TypeScript
2. **API Client** - Axios instance with base URL configuration
3. **Type Definitions** - TypeScript interfaces for API responses
4. **TanStack Query** - Server state management with auto-refetching
5. **Health Status** - Displays API connection status
6. **Testing Setup** - Vitest with React Testing Library
