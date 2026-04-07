from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Board ──────────────────────────────────────────────────────────────────────

class BoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: str  # UUID of the owner profile


class BoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


# ── List ───────────────────────────────────────────────────────────────────────

class ListCreate(BaseModel):
    title: str
    position: float = 0.0
    wip_limit: int = 0


class ListUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[float] = None
    wip_limit: Optional[int] = None


# ── Card ───────────────────────────────────────────────────────────────────────

class CardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    position: float = 0.0
    due_date: Optional[datetime] = None


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[float] = None
    due_date: Optional[datetime] = None


class CardMove(BaseModel):
    list_id: str  # target list UUID
    position: float = 0.0


# ── Comment ────────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    user_id: str  # UUID of the commenter
    content: str


# ── Label ──────────────────────────────────────────────────────────────────────

class LabelCreate(BaseModel):
    name: str
    color: str = "#60a5fa"
    weight: int = 1
