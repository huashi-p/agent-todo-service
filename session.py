from sqlalchemy.orm import Session
from sqlalchemy import select
from database import engine
from models import Todo


with Session(engine) as s:
    try:
        s.add(Todo(content="这个不该留下来"))
        s.flush()
        print("flush 之后同一会话里能看到:", [t.content for t in s.scalars(select(Todo))])
        raise RuntimeError("假装后面出错了")
    except RuntimeError as e:
        s.rollback()
        print("捕获异常并 rollback:", e)

with Session(engine) as s:
    print("回滚之后数据库里:", [t.content for t in s.scalars(select(Todo))])
