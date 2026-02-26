# Frontend

Angular 19 single-page application with TypeScript, Tailwind CSS, and RxJS communicating with the FastAPI backend.

---

## Table of Contents

1. [Local Setup](#local-setup)
2. [Project Structure](#project-structure)
3. [Environment Configuration](#environment-configuration)
4. [Available Scripts](#available-scripts)
5. [Architecture](#architecture)
6. [Running Tests](#running-tests)
7. [Building for Production](#building-for-production)
8. [Docker](#docker)

---

## Local Setup

### Requirements

- Node.js 20 LTS+
- npm 10+

### Install and run

```bash
cd frontend
npm ci
npm start
# Opens http://localhost:4200
```

Or use the project-root shortcut:

```bash
make frontend
```

The frontend dev server proxies API calls to `http://localhost:8000` by default (configured in `proxy.conf.json`). Make sure the backend is running.

### Full stack (recommended)

Start everything from the project root:

```bash
make dev
# Backend:  http://localhost:8000
# Frontend: http://localhost:4200
```

---

## Project Structure

```
frontend/
├── angular.json             ← Angular CLI workspace config
├── package.json             ← Node dependencies
├── tsconfig.json            ← TypeScript base config
├── tsconfig.app.json        ← App-specific TypeScript config
├── tsconfig.spec.json       ← Test TypeScript config
├── karma.conf.js            ← Karma test runner config
├── eslint.config.js         ← ESLint rules
├── postcss.config.mjs       ← PostCSS (Tailwind)
│
├── public/
│   └── favicon.ico
│
├── src/
│   ├── index.html           ← Root HTML shell
│   ├── main.ts              ← Bootstraps Angular application
│   └── styles.css           ← Global styles + Tailwind directives
│
│   └── app/
│       ├── app.component.ts           ← Root component (RouterOutlet)
│       ├── app.routes.ts              ← Route definitions
│       │
│       ├── components/                ← Feature components (one folder per feature)
│       │   ├── login/                 ← Login form
│       │   │   ├── login.component.ts
│       │   │   └── login.component.html
│       │   ├── register/              ← Registration form
│       │   ├── dashboard/             ← Authenticated home page
│       │   ├── game/                  ← Game view and controls
│       │   └── shared/                ← Reusable UI components (buttons, modals)
│       │
│       ├── services/
│       │   ├── api.service.ts         ← Base HTTP client; centralises URL, error handling
│       │   ├── auth.service.ts        ← Login, logout, token storage, authentication state
│       │   ├── game.service.ts        ← Game CRUD operations wrapping api.service
│       │   └── user.service.ts        ← User profile operations
│       │
│       ├── core/
│       │   ├── auth.guard.ts          ← Route guard: redirects to /login if not authenticated
│       │   └── http.interceptor.ts    ← Attaches "Authorization: Bearer <token>" to every request
│       │
│       └── types/                     ← Shared TypeScript interfaces
│           ├── auth.types.ts          ← User, LoginRequest, TokenResponse
│           └── game.types.ts          ← Game, CreateGameRequest, UpdateGameRequest
│
└── Dockerfile               ← Multi-stage build: ng build → nginx
```

---

## Environment Configuration

Angular uses `src/environments/` files to manage per-environment settings.

| File | Used when |
|---|---|
| `src/environments/environment.ts` | `ng serve` (local development) |
| `src/environments/environment.production.ts` | `ng build --configuration production` |

Example `environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000'
};
```

These files are **not secrets** — they contain only public configuration like the API base URL. Sensitive values (auth tokens, keys) are never stored in Angular code.

---

## Available Scripts

```bash
# Development server with hot reload
npm start
# → http://localhost:4200

# Run unit tests with Karma/Jasmine
npm test

# Run tests once (no watch — used in CI)
npm run test:ci

# Type-check without emitting
npm run type-check

# Lint with ESLint
npm run lint

# Auto-fix lint issues
npm run lint:fix

# Production build
npm run build
# Output → dist/

# Analyse bundle size
npm run build -- --stats-json
npx webpack-bundle-analyzer dist/stats.json
```

---

## Architecture

### Data flow

```
User interaction
    │
    ▼
Component (e.g. GameComponent)
    │ calls
    ▼
Service (e.g. GameService)
    │ calls
    ▼
ApiService.get/post/put/delete()
    │
    ▼
HttpClient (Angular)
    │
    ├─ HttpInterceptor adds: Authorization: Bearer <token>
    │
    ▼
Backend API (http://localhost:8000 or https://api.myproject.com)
    │
    ▼
Observable<T> → Component subscribes → updates template
```

### Authentication flow

```
User submits login form
    │
    ▼
AuthService.login(email, password)
    │ POSTs to /auth/login
    ▼
API returns { access_token, refresh_token }
    │
    ▼
AuthService stores tokens in localStorage
    │
    ▼
Router navigates to /dashboard
    │
    ▼
All subsequent requests:
  HttpInterceptor reads token from AuthService
  Adds Authorization header automatically
```

### Route protection

```typescript
// app.routes.ts
{
  path: 'dashboard',
  component: DashboardComponent,
  canActivate: [AuthGuard]   ← redirects to /login if not authenticated
}
```

---

## Running Tests

```bash
# Watch mode (interactive)
npm test

# Single run (used in CI)
npm run test:ci

# With coverage
npm run test:ci -- --code-coverage
open coverage/index.html
```

Tests use **Jasmine** as the test framework and **Karma** as the test runner. Each component and service has a corresponding `.spec.ts` file in the same folder.

Example unit test:
```typescript
// auth.service.spec.ts
describe('AuthService', () => {
  it('should store tokens after login', () => {
    // arrange
    const mockHttp = jasmine.createSpyObj('HttpClient', ['post']);
    mockHttp.post.and.returnValue(of({ access_token: 'token123' }));
    const service = new AuthService(mockHttp);

    // act
    service.login('test@example.com', 'pass').subscribe();

    // assert
    expect(localStorage.getItem('access_token')).toBe('token123');
  });
});
```

---

## Building for Production

```bash
npm run build
# Output: dist/
```

The production build:
- Enables Angular AOT compilation
- Minifies and tree-shakes all JavaScript
- Hashes file names for cache-busting
- Uses `environment.production.ts`

The Docker image serves the `dist/` folder via Nginx with:
- `gzip` compression
- `Cache-Control` headers
- SPA fallback (`try_files $uri /index.html`) for Angular routing

---

## Docker

```bash
# Build
docker build -t myproject-frontend:local ./frontend

# Run
docker run --rm -p 80:80 myproject-frontend:local
# → http://localhost:80

# Multi-stage build internally:
#   Stage 1: node:20-alpine  → npm ci && ng build
#   Stage 2: nginx:alpine    → copies dist/ → serves on :80
```

In CI/CD:
- **Staging:** pushed to GHCR as `ghcr.io/your-org/frontend:staging-<sha>` by `staging.yml`
- **Production:** pushed to ECR as `<account>.dkr.ecr.us-east-1.amazonaws.com/frontend:vX.Y.Z` by `release.yml`
