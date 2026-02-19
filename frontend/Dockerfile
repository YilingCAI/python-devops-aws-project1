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
COPY public ./public

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install http-server to serve the static files
RUN npm install -g http-server

# Copy built app from builder
COPY --from=builder /app/dist/frontend ./dist

# Expose port
EXPOSE 4200

# Start the application
CMD ["http-server", "dist", "-p", "4200"]
