# Source Directory (`src/`)

## Overview

This directory contains all React application source code, organized into logical subdirectories.

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| `components/` | Reusable React components |
| `hooks/` | Custom React hooks |
| `services/` | API client and external services |
| `types/` | TypeScript type definitions |
| `test/` | Test setup and utilities |

## Root Files

| File | Purpose |
|------|---------|
| `main.tsx` | Application entry point, renders App to DOM |
| `App.tsx` | Root component with providers and layout |
| `index.css` | Global CSS styles |
| `vite-env.d.ts` | TypeScript declarations for Vite |

## File Details

### `main.tsx`
**Purpose:** Application bootstrap and DOM mounting

**Packages Used:**
- `react` - React library
- `react-dom/client` - React DOM renderer

**Key Components:**
- `ReactDOM.createRoot()` - Creates React root
- `<StrictMode>` - Enables additional checks

### `App.tsx`
**Purpose:** Root component with global providers

**Packages Used:**
- `@tanstack/react-query` - Server state management
  - `QueryClient` - Query cache and configuration
  - `QueryClientProvider` - Context provider
  - `useQuery` - Data fetching hook

**Key Components:**
- `queryClient` - TanStack Query client instance
- `HealthStatus` - Displays API health
- `AppContent` - Main application layout

### `index.css`
**Purpose:** Global styles and CSS variables

**Features:**
- CSS custom properties (variables)
- Dark/light mode support
- Responsive layout styles

## Import Conventions

```typescript
// External packages first
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// Internal imports with path aliases or relative paths
import { healthCheck } from './services/api';
import type { HealthResponse } from './types';
```

## Component Pattern

Components follow this structure:
```typescript
// ComponentName.tsx

// Imports
import { useState } from 'react';

// Types (if component-specific)
interface Props {
  title: string;
}

// Component
export function ComponentName({ title }: Props) {
  return <div>{title}</div>;
}

// Or default export
export default ComponentName;
```
