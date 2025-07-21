import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime

from . import models

def import_schedule_from_excel(db: Session, file_path: str) -> str:
    """
    从Excel文件导入值班表到数据库。

    核心流程:
    1. 使用pandas读取Excel文件。
    2. 假设Excel有两列：'日期' (YYYY-MM-DD格式) 和 '姓名'。
    3. 清理已存在的旧排班数据。
    4. 遍历Excel中的每一行，创建DutySchedule对象。
    5. 将所有新对象批量添加到数据库并提交。

    Args:
        db (Session): SQLAlchemy数据库会话。
        file_path (str): Excel文件的本地路径。

    Returns:
        str: 操作结果信息。
    """
    try:
        # 1. 使用pandas读取Excel
        df = pd.read_excel(file_path, engine='openpyxl')

        # === 健壮性升级：从“名称映射”升级为“位置映射” ===
        # 我们不再依赖具体的列名，而是依赖列的位置。
        # 核心假设：第一列为日期，后续四列为按顺序的值班员。
        
        column_names = df.columns.tolist()

        # 检查列的数量，确保至少有5列
        if len(column_names) < 5:
            return f"错误：Excel文件必须至少包含5列（1个日期列和4个值班人员列）。检测到 {len(column_names)} 列。"

        # 按位置动态分配列名
        date_col = column_names[0]
        full_prof_col = column_names[1]
        cs_complaint_col = column_names[2]
        cs_fault_col = column_names[3]
        ps_prof_col = column_names[4]

    except FileNotFoundError:
        return f"错误：文件未找到于路径 '{file_path}'。"
    except Exception as e:
        return f"读取Excel文件时发生未知错误: {e}"

    try:
        # 2. 清理旧数据 (这是一个可选的业务决策，这里假设每次导入都是全新的排班)
        num_deleted = db.query(models.DutySchedule).delete()
        db.commit()

        # 3. 准备新数据
        new_schedules = []
        for index, row in df.iterrows():
            # 跳过日期为空的行
            if pd.isna(row[date_col]):
                continue
            
            # 将pandas的Timestamp对象转换为Python的date对象
            duty_date_obj = pd.to_datetime(row[date_col]).date()
            
            # 使用动态获取的列名来安全地获取数据
            schedule = models.DutySchedule(
                duty_date=duty_date_obj,
                employee_full_professional=row.get(full_prof_col),
                employee_cs_complaint=row.get(cs_complaint_col),
                employee_cs_fault=row.get(cs_fault_col),
                employee_ps_professional=row.get(ps_prof_col)
            )
            new_schedules.append(schedule)

        # 4. 批量插入新数据
        db.add_all(new_schedules)
        db.commit()

        return f"成功！清除了 {num_deleted} 条旧记录，并成功导入了 {len(new_schedules)} 条新值班记录。"

    except Exception as e:
        db.rollback() # 如果发生错误，回滚事务
        return f"数据库操作失败: {e}"

def get_duty_employee(db: Session, duty_date_str: str) -> str:
    """
    查询指定日期的值班人员。

    Args:
        db (Session): SQLAlchemy数据库会话。
        duty_date_str (str): 日期字符串, 格式为 "YYYY-MM-DD" 或 "today"。

    Returns:
        str: 查询结果。可能是员工姓名，也可能是提示信息。
    """
    try:
        if duty_date_str.lower() == "today":
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(duty_date_str, "%Y-%m-%d").date()
    except ValueError:
        return f"日期格式错误。请输入 'YYYY-MM-DD' 格式或 'today'。"

    try:
        schedule = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == target_date).first()
        
        if schedule:
            response_lines = [f"{target_date.strftime('%Y年%m月%d日')} 的值班安排如下:"]
            response_lines.append(f"  - 全专业值班: {schedule.employee_full_professional or '无安排'}")
            response_lines.append(f"  - CS专业投诉值班: {schedule.employee_cs_complaint or '无安排'}")
            response_lines.append(f"  - CS专业故障值班: {schedule.employee_cs_fault or '无安排'}")
            response_lines.append(f"  - PS专业值班: {schedule.employee_ps_professional or '无安排'}")
            return "\n".join(response_lines)
        else:
            return f"未找到 {target_date.strftime('%Y年%m月%d日')} 的值班记录。"
    
    except Exception as e:
        return f"查询数据库时发生错误: {e}"

# 角色名到模型字段名的映射
ROLE_TO_FIELD_MAP = {
    '全专业值班': 'employee_full_professional',
    'CS专业投诉值班': 'employee_cs_complaint',
    'CS专业故障值班': 'employee_cs_fault',
    'PS专业值班': 'employee_ps_professional'
}

def swap_duty_schedule(db: Session, date1_str: str, role1: str, date2_str: str, role2: str) -> str:
    """
    精准交换两个指定日期的特定专业的值班人员。

    这是一个事务性操作。

    Args:
        db (Session): SQLAlchemy数据库会话。
        date1_str (str): 第一个日期字符串 ("YYYY-MM-DD")。
        role1 (str): 第一个日期对应的专业名称。
        date2_str (str): 第二个日期字符串 ("YYYY-MM-DD")。
        role2 (str): 第二个日期对应的专业名称。

    Returns:
        str: 操作结果信息。
    """
    if role1 not in ROLE_TO_FIELD_MAP:
        return f"错误：无效的专业名称 '{role1}'。有效名称为: {list(ROLE_TO_FIELD_MAP.keys())}"
    if role2 not in ROLE_TO_FIELD_MAP:
        return f"错误：无效的专业名称 '{role2}'。有效名称为: {list(ROLE_TO_FIELD_MAP.keys())}"

    try:
        d1 = datetime.strptime(date1_str, "%Y-%m-%d").date()
        d2 = datetime.strptime(date2_str, "%Y-%m-%d").date()
    except ValueError:
        return "日期格式错误。请输入 'YYYY-MM-DD' 格式。"

    try:
        # 在一个会话中查询两个记录
        schedule1 = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == d1).first()
        schedule2 = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == d2).first()

        if not schedule1:
            return f"未找到 {date1_str} 的值班记录，无法换班。"
        if not schedule2:
            return f"未找到 {date2_str} 的值班记录，无法换班。"

        field1 = ROLE_TO_FIELD_MAP[role1]
        field2 = ROLE_TO_FIELD_MAP[role2]

        # 使用getattr和setattr动态地获取和设置属性
        name1 = getattr(schedule1, field1)
        name2 = getattr(schedule2, field2)
        
        setattr(schedule1, field1, name2)
        setattr(schedule2, field2, name1)

        db.commit() # 提交事务

        return (f"成功！已将 {date1_str} 的 '{role1}' ({name1 or '无'}) "
                f"与 {date2_str} 的 '{role2}' ({name2 or '无'}) 进行了对调。")

    except Exception as e:
        db.rollback()
        return f"数据库操作失败，已回滚: {e}"
