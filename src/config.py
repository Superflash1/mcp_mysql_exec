import os
from dotenv import load_dotenv

# 再次修正: 明确使用 'gbk' 编码加载 .env 文件。
# 这是处理在中国区Windows环境下创建的文本文件的最可靠方法。
load_dotenv(encoding="gbk")

# --- 数据库配置 ---
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "duty_schedule_db")

# 构建数据库连接URL
# 注意：需要确保你的mysql-connector-python版本和SQLAlchemy兼容
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
