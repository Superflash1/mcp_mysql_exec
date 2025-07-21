from sqlalchemy.orm import Session
from mcp import tool # 假设MCP框架提供了tool装饰器

from . import services
from .database import SessionLocal, engine, Base, get_db
from .models import DutySchedule

# --- 数据库初始化 ---
# 在服务启动时确保数据库表已创建
print("正在初始化数据库，检查并创建表...")
try:
    Base.metadata.create_all(bind=engine)
    print("数据库表检查完成。")
except Exception as e:
    print(f"数据库初始化失败: {e}")
    # 在实际生产中，这里可能需要更复杂的错误处理
    exit(1)


# --- MCP 工具定义 ---

@tool
def import_schedule_from_excel(file_path: str) -> str:
    """
    从本地Excel文件导入值班表数据到MySQL数据库。
    此操作会先清空旧的值班数据，然后导入新数据。
    Excel文件必须包含名为 '日期' 和 '姓名' 的两列。
    
    :param file_path: Excel文件的绝对或相对路径。
    :return: 一个描述操作结果的字符串。
    """
    db = next(get_db())
    try:
        result = services.import_schedule_from_excel(db, file_path)
        return result
    finally:
        db.close()

@tool
def get_duty_employee(duty_date: str) -> str:
    """
    查询指定日期的完整值班安排。
    
    :param duty_date: 要查询的日期，格式为 'YYYY-MM-DD'，或者使用 'today' 来查询当天。
    :return: 一个格式化的、包含所有专业值班人员信息的字符串。
    """
    db = next(get_db())
    try:
        result = services.get_duty_employee(db, duty_date)
        return result
    finally:
        db.close()

@tool
def swap_duty_schedule(date1: str, role1: str, date2: str, role2: str) -> str:
    """
    精准对调两个指定日期的特定专业的值班人员。
    
    :param date1: 第一个要交换的日期，格式 'YYYY-MM-DD'。
    :param role1: 第一个日期要交换的专业名称。必须是 ['全专业值班', 'CS专业投诉值班', 'CS专业故障值班', 'PS专业值班'] 之一。
    :param date2: 第二个要交换的日期，格式 'YYYY-MM-DD'。
    :param role2: 第二个日期要交换的专业名称。必须是 ['全专业值班', 'CS专业投诉值班', 'CS专业故障值班', 'PS专业值班'] 之一。
    :return: 一个描述操作结果的字符串。
    """
    db = next(get_db())
    try:
        result = services.swap_duty_schedule(db, date1, role1, date2, role2)
        return result
    finally:
        db.close()

# 你可以在这里添加一个 if __name__ == '__main__': 块来进行本地测试
# 例如：
# if __name__ == '__main__':
#     print("执行本地测试...")
#     # 1. 准备一个测试用的 .env 文件和 test_schedule.xlsx 文件
#     # 2. 调用工具函数
#     print(import_schedule_from_excel("path/to/your/test_schedule.xlsx"))
#     print(get_duty_employee("2024-10-01"))
#     print(swap_duty_schedule("2024-10-01", "2024-10-02"))
