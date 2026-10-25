from sqlalchemy import text

from database import DATABASE_URL, engine

print("连接串:", DATABASE_URL)

with engine.connect() as conn:
    print("PostgreSQL 版本:", conn.execute(text("select version()")).scalar())