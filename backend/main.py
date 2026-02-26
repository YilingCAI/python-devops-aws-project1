"""
FastAPI Application Entry Point

Initializes:
- Environment configuration (.env loading)
- Structured logging
- Security middleware
- CORS configuration
- API routes
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api import users, health, game

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
# Load environment variables in order of precedence:
# 1. System environment variables (already set)
# 2. config/.env.dev (development) or config/.env.test (testing)
env_files = [
    Path(__file__).parent.parent / "config" / ".env.dev"
]
for env_path in env_files:
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"Loaded environment from {env_path}")
    else:
        print(f"⚠ {env_path} not found, skipping")

# ============================================================================
# LOGGING SETUP
# ============================================================================
setup_logging()
logger = get_logger(__name__)

# ============================================================================
# CREATE FASTAPI APP
# ============================================================================
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if not settings.IS_PRODUCTION else None,
    redoc_url="/redoc" if not settings.IS_PRODUCTION else None,
    openapi_url="/openapi.json" if not settings.IS_PRODUCTION else None,
)

logger.info(
    "FastAPI application initialized",
    extra={
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_version": settings.API_VERSION,
    },
)

# ============================================================================
# PRODUCTION VALIDATION
# ============================================================================
if settings.IS_PRODUCTION:
    try:
        settings.validate_production()
        logger.info("Production configuration validated successfully")
    except ValueError as e:
        logger.critical(f"Production validation failed: {e}")
        raise

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS_LIST,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_METHODS_LIST,
    allow_headers=settings.CORS_HEADERS_LIST,
)

logger.info(
    "CORS middleware configured",
    extra={
        "allowed_origins": settings.ORIGINS_LIST,
        "credentials": settings.CORS_ALLOW_CREDENTIALS,
    },
)

# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Standard security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS (only in production)
    if settings.IS_PRODUCTION or settings.ENABLE_HSTS:
        response.headers["Strict-Transport-Security"] = (
            f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains"
        )
    
    # CSP (Content Security Policy)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    
    return response

# ============================================================================
# LOGGING MIDDLEWARE
# ============================================================================
@app.middleware("http")
async def log_requests(request, call_next):
    """Log incoming requests and responses."""
    import time
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Track timing
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log successful request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
            exc_info=True,
        )
        raise

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================
app.include_router(health.router, tags=["Health"])
app.include_router(users.router, tags=["Users"])
app.include_router(game.router, tags=["Game"])

logger.info(
    "All routers registered",
    extra={
        "routes": ["health", "users", "game"],
    },
)

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(
        "Application startup",
        extra={
            "environment": settings.ENVIRONMENT,
            "database": f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}",
        },
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Application shutdown")

# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"{settings.PROJECT_NAME} API",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        workers=settings.BACKEND_WORKERS if not settings.BACKEND_RELOAD else 1,
    )
