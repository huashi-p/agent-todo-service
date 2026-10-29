from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TodoIn(BaseModel):
    content: str = Field(min_length=1, max_length=200)
    done: bool = False
    user_id: int | None = None


class TodoDone(BaseModel):
    done: bool


class TodoOut(BaseModel):
    id: int
    content: str
    done: bool
    created_at: datetime
    user_id: int | None
    user: UserBrief | None = None

    model_config = {"from_attributes": True}

class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class UserOut(BaseModel):
    id: int
    name: str
    todos: list[TodoOut] = []

    model_config = {"from_attributes": True}

class UserWithCount(BaseModel):
    id: int
    name: str
    todo_count: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=200,
    )
