from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

# -------------------------
# Base Schema (Shared Fields)
# -------------------------
class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username"
    )


# -------------------------
# Register Schema
# -------------------------
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a number")
        return v


# -------------------------
# Login Schema
# -------------------------
class UserLogin(BaseModel):
    username: str
    password: str


# -------------------------
# Response Schema
# -------------------------
class UserResponse(UserBase):
    id: int
    wins: int

    model_config = ConfigDict(
        from_attributes=True  # Required for SQLAlchemy ORM
    )