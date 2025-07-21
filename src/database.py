import mysql.connector
from mysql.connector import errorcode
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DATABASE_URL

def ensure_database_exists():
    """在创建SQLAlchemy引擎前，确保数据库本身存在"""
    try:
        # 1. 先不带数据库名连接，以检查和创建数据库
        cnx = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = cnx.cursor()
        
        # 2. 使用参数化查询来安全地创建数据库
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
            print(f"数据库 '{DB_NAME}' 已成功创建。")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DB_CREATE_EXISTS:
                # 数据库已存在，这是正常情况
                pass
            else:
                print(err)
        
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        print(f"数据库连接或创建失败: {err}")
        exit(1) # 如果无法连接或创建数据库，则终止程序

# 在模块加载时执行数据库存在性检查
ensure_database_exists()

# 创建数据库引擎
# 现在我们可以安全地使用包含数据库名的URL
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
