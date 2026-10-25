from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine
from models import Todo

with Session(engine) as session:
    item = Todo(content="第一条真实数据")
    session.add(item)
    session.commit()
    print("新记录 id:", item.id)

with Session(engine) as session:
    items = session.scalars(select(Todo)).all()
    for t in items:
        print(t.id, t.content, t.done, t.created_at)