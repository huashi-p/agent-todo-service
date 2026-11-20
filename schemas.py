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


class ParsedJob(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=2000)
    deadline: datetime | None = None
    requirements: list[str] = Field(default_factory=list, max_length=30)

class JobApplicationCreateRequest(BaseModel):
    company: str = Field(
        min_length=1,
        max_length=200,
    )
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str = Field(
        min_length=10,
        max_length=20000,
    )
    location: str | None = Field(
        default=None,
        max_length=200,
    )
    deadline: datetime | None = None
    requirements: list[str] = Field(
        default_factory=list,
        max_length=30,
    )


class JobDescriptionParseRequest(BaseModel):
    description: str = Field(
        min_length=10,
        max_length=30000,
    )


class ApplicationStatusUpdateRequest(BaseModel):
    new_status: Literal[
        "applied",
        "assessment",
        "first_interview",
        "second_interview",
        "hr_interview",
        "offer",
        "rejected",
        "withdrawn",
    ]
    note: str = Field(
        default="",
        max_length=1000,
    )


class ApplicationTaskCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    task_type: Literal[
        "skill_gap",
        "interview_preparation",
        "follow_up",
        "assessment",
    ] = "interview_preparation"
    due_at: datetime | None = None
    note: str = Field(
        default="",
        max_length=2000,
    )


class LearningPlanDraftRequest(BaseModel):
    available_hours_per_week: int = Field(
        default=10,
        ge=1,
        le=40,
    )


class LearningPlanSaveRequest(BaseModel):
    available_hours_per_week: int = Field(
        default=10,
        ge=1,
        le=40,
    )
    items: list[dict]
    confirmed: bool = False

class ResourceSourceStatus(BaseModel):
    url: str
    final_url: str | None = None
    ok: bool
    status_code: int = 0
    title: str = ""
    text: str = ""
    elapsed_ms: float = 0
    error: str = ""

class GroundedLearningPlanDraftRequest(BaseModel):
    available_hours_per_week: int = Field(
        default=10,
        ge=1,
        le=40,
    )
