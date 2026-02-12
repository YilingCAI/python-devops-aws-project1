from app.db.session import Base
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy import CheckConstraint

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    wins = Column(Integer, default=0, nullable=False)

    # Relationships
    games_as_player1 = relationship(
        "Game",
        foreign_keys="Game.player1",
        back_populates="player1_user"
    )

    games_as_player2 = relationship(
        "Game",
        foreign_keys="Game.player2",
        back_populates="player2_user"
    )


class Game(Base):
    __tablename__ = "games"


    __table_args__ = (
        CheckConstraint("player1 != player2", name="check_players_different"),
    )

    game_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    player1 = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    player2 = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    board = Column(JSON, nullable=False)

    current_turn = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    winner = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    status = Column(String(20), nullable=False, server_default="in_progress")

    # Relationships
    player1_user = relationship(
        "User",
        foreign_keys=[player1],
        back_populates="games_as_player1"
    )

    player2_user = relationship(
        "User",
        foreign_keys=[player2],
        back_populates="games_as_player2"
    )

    current_turn_user = relationship(
        "User",
        foreign_keys=[current_turn]
    )

    winner_user = relationship(
        "User",
        foreign_keys=[winner]
    )