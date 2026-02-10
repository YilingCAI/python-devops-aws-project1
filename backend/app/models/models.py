from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default = True)
    role = Column(String)


class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))


"""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    wins INTEGER DEFAULT 0
);



CREATE TABLE games (
    game_id UUID PRIMARY KEY,
    player1 VARCHAR(50) REFERENCES users(username),
    player2 VARCHAR(50) REFERENCES users(username),
    board CHAR(9) NOT NULL,
    current_turn VARCHAR(50),
    winner VARCHAR(50)
);
"""