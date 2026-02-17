# Frontend - Angular (Tic Tac Toe Game)

This is the Angular implementation of the Tic Tac Toe game frontend, refactored from React/Next.js.

## Technology Stack

- **Framework**: Angular 19
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 4
- **HTTP Client**: Angular HttpClient
- **Routing**: Angular Router
- **State Management**: RxJS with Services and Observables
- **Testing**: Jasmine & Karma
- **Build Tool**: Angular CLI

## Prerequisites

- Node.js 18+ (or use nvm)
- npm or yarn

### Install Node.js with nvm (Optional)

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js LTS
nvm install --lts
nvm use --lts
node -v   # Node.js version, e.g., v20.x.x
npm -v    # npm version, e.g., 10.x.x
```

## Setup

### Installation

```bash
npm install
```

### Development Server

```bash
npm start
```

Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

### Build

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
npm run lint:fix
```

## Project Structure

```
src/
├── app/
│   ├── components/          # Angular components
│   │   ├── login/
│   │   ├── signup/
│   │   ├── homepage/
│   │   ├── game-board/
│   │   ├── create-game/
│   │   └── join-game/
│   ├── services/            # Services (API, Auth, Game)
│   ├── core/               # Core functionality (guards, interceptors)
│   ├── types/              # TypeScript interfaces
│   ├── app.component.ts    # Root component
│   ├── app.routes.ts       # Route configuration
│   └── app.module.ts       # App module
├── environments/           # Environment configuration
├── index.html             # HTML entry point
├── main.ts                # Bootstrap file
├── polyfills.ts           # Browser polyfills
└── styles.css             # Global styles
```

## Key Features

### Authentication
- User registration and login
- JWT token-based authentication
- Automatic token refresh via interceptors
- Protected routes with AuthGuard

### Game Features
- Create new tic-tac-toe games
- Join existing games by game ID
- Real-time move updates
- Game state management
- Win/loss tracking

### Architecture
- **Standalone Components**: Modern Angular with standalone components
- **Dependency Injection**: Services for API, Auth, and Game logic
- **HTTP Interceptors**: Automatic token injection and error handling
- **Reactive Programming**: RxJS observables for state management
- **Type Safety**: Full TypeScript with strict mode

## API Integration

The frontend integrates with the backend API at `http://localhost:8000`:

### Authentication Endpoints
- `POST /users/register` - Register new user
- `POST /users/login` - User login
- `GET /users/me` - Get current user profile

### Game Endpoints
- `POST /games/create_game` - Create new game
- `POST /games/{game_id}/join` - Join existing game
- `POST /games/move` - Make a move
- `GET /games` - Get user's games
- `GET /games/{game_id}` - Get specific game

## Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Docker

Build and run the frontend in Docker:

```bash
# Build
docker build -t tic-tac-toe-frontend .

# Run
docker run -p 4200:4200 \
  -e NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
  tic-tac-toe-frontend
```

## Component Documentation

See [ANGULAR_MIGRATION.md](./ANGULAR_MIGRATION.md) for detailed architecture and component documentation.

## Deployment

### Development
```bash
npm start
```

### Production
```bash
npm run build
# Serve the dist/frontend directory
```

## Troubleshooting

### Port already in use
```bash
# Change the default port in angular.json or use:
ng serve --port 4300
```

### API connection issues
- Ensure the backend is running on `http://localhost:8000`
- Check `environment.ts` for correct API URL
- Verify CORS settings on the backend

### Build errors
```bash
# Clear cache and reinstall
rm -rf node_modules dist
npm install
npm run build
```

## Migration Notes

This project was migrated from React/Next.js to Angular with the following improvements:
- Stronger type safety with Angular's TypeScript implementation
- Better state management with RxJS and Services
- Built-in dependency injection
- Enhanced routing with guards
- Better testing infrastructure with Jasmine/Karma
- Improved component lifecycle management

## Support & Documentation

- [Angular Documentation](https://angular.io/docs)
- [Angular CLI Documentation](https://angular.io/cli)
- [RxJS Documentation](https://rxjs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
