import json

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from agent import run_agent
from cache import TODOS_CACHE_KEY, cache_clear, cache_get, cache_set
from database import Base, engine, get_db

from models import (
    ApplicationStatusEvent,
    ApplicationTask,
    JobApplication,
    Todo,
    User,
)
from schemas import AskRequest, TodoDone, TodoIn, TodoOut, UserIn, UserOut
import asyncio
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"
app = FastAPI(default_response_class=UTF8JSONResponse)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "offerflow",
    }


AGENT_TIMEOUT = 60.0


@app.get("/stream")
async def stream():
    async def events():
        for i in range(5):
            yield f"data: 第 {i} 条\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    existing = db.scalars(select(User).where(User.name == user.name)).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="这个名字已经存在")
    item = User(name=user.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(selectinload(User.todos))).all()
    return [{"name": u.name, "todos": len(u.todos)} for u in users]

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.todos))
    )
    item = db.scalars(stmt).first()
    if item is None:
        raise HTTPException(status_code=404, detail="没有这个用户")
    return item


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(todo: TodoIn, db: Session = Depends(get_db)):
    if todo.user_id is not None and db.get(User, todo.user_id) is None:
        raise HTTPException(status_code=404, detail="没有这个用户")
    item = Todo(content=todo.content, done=todo.done, user_id=todo.user_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    cache_clear(TODOS_CACHE_KEY)
    return item


@app.get("/todos", response_model=list[TodoOut])
def list_todos(done: bool | None = None, db: Session = Depends(get_db)):
    if done is None:
        cached = cache_get(TODOS_CACHE_KEY)
        if cached is not None:
            return json.loads(cached)

    stmt = select(Todo).options(selectinload(Todo.user))
    if done is not None:
        stmt = stmt.where(Todo.done == done)
    items = db.scalars(stmt).all()

    if done is None:
        payload = [
            TodoOut.model_validate(item).model_dump(mode="json") for item in items
        ]
        cache_set(TODOS_CACHE_KEY, json.dumps(payload, ensure_ascii=False))
    return items


@app.get("/todos/page", response_model=list[TodoOut])
def page_todos(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Todo)
        .options(selectinload(Todo.user))
        .order_by(Todo.id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()

@app.get("/todos/count")
def count_todos(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Todo))
    return {"count": total}

@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    item = db.get(Todo, todo_id)
    if item is None:
        raise HTTPException(status_code=404, detail="没有这个任务")
    return item


@app.patch("/todos/{todo_id}/done", response_model=TodoOut)
def set_todo_done(todo_id: int, body: TodoDone, db: Session = Depends(get_db)):
    item = db.get(Todo, todo_id)
    if item is None:
        raise HTTPException(status_code=404, detail="没有这个任务")
    item.done = body.done
    db.commit()
    db.refresh(item)
    cache_clear(TODOS_CACHE_KEY)
    return item

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    item = db.get(User, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="没有这个用户")
    db.delete(item)
    db.commit()
    cache_clear(TODOS_CACHE_KEY)
    return None



@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    item = db.get(Todo, todo_id)
    if item is None:
        raise HTTPException(status_code=404, detail="没有这个任务")
    db.delete(item)
    db.commit()
    cache_clear(TODOS_CACHE_KEY)
    return None


async def ask_stream_events(question: str, history):
    yield "event: status\ndata: 正在整理上下文\n\n"
    yield "event: status\ndata: 正在思考\n\n"

    try:
        answer = await asyncio.wait_for(
            run_agent(question, history=history),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        yield "event: error\ndata: 模型太久没回应\n\n"
        return
    except Exception as e:
        message = str(e).replace("\n", " ")
        yield f"event: error\ndata: 模型调用失败：{message}\n\n"
        return

    answer = answer or ""

    for ch in answer:
        if ch == "\n":
            ch = "\\n"

        yield f"event: token\ndata: {ch}\n\n"
        await asyncio.sleep(0.03)

    yield "event: done\ndata: [DONE]\n\n"

@app.get("/api/applications")
def list_application_records(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    items = db.scalars(
        select(JobApplication)
        .order_by(JobApplication.updated_at.desc())
        .limit(limit)
    ).all()

    return {
        "count": len(items),
        "applications": [
            {
                "id": item.id,
                "company": item.company,
                "title": item.title,
                "location": item.location,
                "current_status": item.current_status,
                "deadline": item.deadline,
                "updated_at": item.updated_at,
            }
            for item in items
        ],
    }
@app.get("/api/applications/{application_id}")
def get_application_detail(
    application_id: int,
    db: Session = Depends(get_db),
):
    item = db.get(JobApplication, application_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="没有这个投递记录",
        )

    events = db.scalars(
        select(ApplicationStatusEvent)
        .where(ApplicationStatusEvent.application_id == application_id)
        .order_by(ApplicationStatusEvent.created_at)
    ).all()

    tasks = db.scalars(
        select(ApplicationTask)
        .where(ApplicationTask.application_id == application_id)
        .order_by(ApplicationTask.created_at)
    ).all()

    return {
        "id": item.id,
        "company": item.company,
        "title": item.title,
        "location": item.location,
        "source_url": item.source_url,
        "current_status": item.current_status,
        "deadline": item.deadline,
        "requirements": list(item.requirements or []),
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "history": [
            {
                "from_status": event.from_status,
                "to_status": event.to_status,
                "note": event.note,
                "created_at": event.created_at,
            }
            for event in events
        ],
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "due_at": task.due_at,
                "status": task.status,
                "note": task.note,
            }
            for task in tasks
        ],
    }

@app.post("/ask/stream")
async def ask_stream(request: AskRequest):
    return StreamingResponse(
        ask_stream_events(
            request.question,
            request.history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
