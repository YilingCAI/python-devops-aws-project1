# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig*.json ./
COPY angular.json ./
COPY postcss.config.mjs ./

# Install dependencies
RUN npm install
RUN npm ci

# Copy source code
COPY src ./src

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config with SPA fallback (try_files → index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder — Angular 19 (browser builder) outputs to dist/frontend
COPY --from=builder /app/dist/frontend /usr/share/nginx/html

# Expose port
EXPOSE 4200

# Start nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
