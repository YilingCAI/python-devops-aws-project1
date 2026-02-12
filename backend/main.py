from fastapi import FastAPI
from app.api import users, health, game
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Game API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Include routers
app.include_router(game.router)
app.include_router(users.router)
app.include_router(health.router)
