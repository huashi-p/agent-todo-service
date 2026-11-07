from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, engine


def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    todos: Mapped[list["Todo"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)

    user: Mapped["User | None"] = relationship(back_populates="todos")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200), default=None)
    source_url: Mapped[str | None] = mapped_column(String(2000), default=None)
    description: Mapped[str] = mapped_column(Text)
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    current_status: Mapped[str] = mapped_column(
        String(40),
        default="applied",
    )
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )




class ApplicationStatusEvent(Base):
    __tablename__ = "application_status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(
        String(40),
        default=None,
    )
    to_status: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text, default="")
    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EvidenceDocument(Base):
    __tablename__ = "evidence_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    project_name: Mapped[str | None] = mapped_column(
        String(200),
        default=None,
    )
    source_label: Mapped[str | None] = mapped_column(
        String(500),
        default=None,
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EvidenceChunk(Base):
    __tablename__ = "evidence_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("evidence_documents.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

class SkillRequirement(Base):
    __tablename__ = "skill_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        index=True,
    )
    requirement: Mapped[str] = mapped_column(Text)
    importance: Mapped[str] = mapped_column(
        String(20),
        default="must_have",
    )
    current_status: Mapped[str] = mapped_column(String(20))
    target_level: Mapped[str] = mapped_column(
        String(10),
        default="L3",
    )
    gap_type: Mapped[str] = mapped_column(
        String(30),
        default="",
    )
    evidence_ids: Mapped[list[int]] = mapped_column(
        JSON,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

class LearningPlanItem(Base):
    __tablename__ = "learning_plan_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        index=True,
    )
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("skill_requirements.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    objective: Mapped[str] = mapped_column(Text)
    target_level: Mapped[str] = mapped_column(String(10))
    steps: Mapped[list[str]] = mapped_column(JSON, default=list)
    exercise: Mapped[str] = mapped_column(Text)
    deliverable: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
    )
    sources: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
    )
    estimated_hours: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    
class ApplicationTask(Base):
    __tablename__ = "application_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    task_type: Mapped[str] = mapped_column(String(40))
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


Base.metadata.create_all(bind=engine)
