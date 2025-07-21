from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL

# 创建数据库引擎
# connect_args 是为了处理特定于mysql-connector-python的选项
engine = create_engine(
    DATABASE_URL,
    # echo=True  # 如果需要查看SQLAlchemy生成的SQL语句，可以取消此行注释
)

# 创建一个数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个所有ORM模型将要继承的基类
Base = declarative_base()

# 数据库依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
