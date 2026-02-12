import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, Game
from app.schemas.game import GameCreate, MoveRequest, GameResponse
from app.services.game_logic import check_winner
from app.core.security import get_current_user  # JWT-based dependency
from typing import Optional

router = APIRouter(
    prefix="/games",
    tags=["Games"]
)

# -----------------------------
# Create a new game
# -----------------------------
# -----------------------------
# Create a new game
# -----------------------------
@router.post("/create_game", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    payload: Optional[GameCreate] = None,  # if you want extra info later
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new game for the current user. Player2 is optional and can join later.
    """

    new_game = Game(
        game_id=uuid.uuid4(),
        player1=current_user.id,
        player2=None,               # nullable, will join later
        board=[" "] * 9,            # initialize empty board as JSON list
        current_turn=current_user.id,
        winner=None,
        status="in_progress" 
    )

    db.add(new_game)
    db.commit()
    db.refresh(new_game)

    return new_game


# -----------------------------
# Make a move
# -----------------------------
@router.post("/move")
def make_move(payload: MoveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Fetch the game and lock it for update
    game = (
        db.query(Game)
        .filter(Game.game_id == payload.game_id)
        .with_for_update()
        .first()
    )

    if not game:
        raise HTTPException(status_code=400, detail="Invalid game ID")

    if game.winner:
        return {
            "message": "Game already finished",
            "board": game.board,
            "winner": game.winner
        }

    if game.current_turn != current_user.id:
        raise HTTPException(status_code=400, detail="Not your turn")

    if payload.move < 0 or payload.move > 8:
        raise HTTPException(status_code=400, detail="Invalid move position")

    if game.board[payload.move] != " ":
        raise HTTPException(status_code=400, detail="Cell already taken")

    # Apply move
    symbol = "X" if game.current_turn == game.player1 else "O"
    game.board[payload.move] = symbol

    winner = check_winner(game.board)

    if winner == "Draw":
        game.winner = None
        game.status = "finished"

    elif winner:
        winner_id = game.player1 if winner == "X" else game.player2
        game.winner = winner_id
        game.status = "finished"

        winner_user = db.query(User).filter(User.id == winner_id).first()
        winner_user.wins += 1

    else:
        game.current_turn = (
            game.player2 if game.current_turn == game.player1 else game.player1
        )

    db.commit()
    db.refresh(game)

    return {
        "message": "Move applied",
        "board": game.board,
        "current_turn": game.current_turn,
        "winner": game.winner
    }


# -----------------------------
# Get game state
# -----------------------------
@router.get("/{game_id}", response_model=GameResponse)
def get_game_state(game_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=400, detail="Invalid game ID")

    # Optional: restrict to players only
    if current_user.id not in [game.player1, game.player2]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a player in this game")

    return game