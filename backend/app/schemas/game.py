from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

# -----------------------------
# Create Game
# -----------------------------
class GameCreate(BaseModel):
    # No username needed anymore — we get current_user from JWT
    pass  # Keep it empty if creating a game just uses the current user


# -----------------------------
# Make a Move
# -----------------------------
class MoveRequest(BaseModel):
    game_id: UUID
    move: int  # 0-8 for board index


# -----------------------------
# Game Response
# -----------------------------
class GameResponse(BaseModel):
    game_id: UUID
    player1: int
    player2: Optional[int] = None
    board: List[str]
    current_turn: Optional[int] = None
    winner: Optional[int] = None
    status: str

    class Config:
        orm_mode = True