from sqlalchemy import select
from sqlalchemy.orm import Session
from database import engine
from models import Todo


with Session(engine) as db:
    item = Todo(content="要改的任务")
    db.add(item)
    db.commit()
    db.refresh(item)
    todo_id = item.id
    print("增:",todo_id,item.content)


with Session(engine) as db:
    one = db.get(Todo,todo_id)
    print("查单条:",one.id,one.content)

    one.done = True
    db.commit()
    print("改完 done:", db.get(Todo, todo_id).done)

    db.delete(one)
    db.commit()
    print("删完再查:", db.get(Todo, todo_id))

    rest = db.scalars(select(Todo)).all()
    print("剩下的条数:",len(rest))










































