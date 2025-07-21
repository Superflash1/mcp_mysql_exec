import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import base64
import os
import io
from typing import Optional

from . import models, schemas

# --- 内部辅助函数 ---

def _normalize_path(file_path: str) -> str:
    """
    Cleans and normalizes a file path to be OS-agnostic and user-friendly.
    """
    # 1. 去除首尾可能存在的空格
    cleaned_path = file_path.strip()
    
    # 2. 去除首尾可能存在的引号
    if (cleaned_path.startswith('"') and cleaned_path.endswith('"')) or \
       (cleaned_path.startswith("'") and cleaned_path.endswith("'")):
        cleaned_path = cleaned_path[1:-1]
    
    # 3. 将所有反斜杠统一替换为正斜杠
    cleaned_path = cleaned_path.replace('\\', '/')
    
    # 4. 展开用户目录
    cleaned_path = os.path.expanduser(cleaned_path)
    
    # 5. 规范化路径
    cleaned_path = os.path.normpath(cleaned_path)
    
    return cleaned_path

# 角色名到数据库模型字段名的映射
ROLE_TO_FIELD_MAP = {
    '全专业值班': 'employee_full_professional',
    'CS专业投诉值班': 'employee_cs_complaint',
    'CS专业故障值班': 'employee_cs_fault',
    'PS专业值班': 'employee_ps_professional'
}
FIELD_TO_ROLE_MAP = {v: k for k, v in ROLE_TO_FIELD_MAP.items()} # 反向映射，方便使用

def _read_and_process_excel(db: Session, excel_source) -> schemas.GeneralResponse:
    """内部核心函数，读取Excel并处理数据，返回结构化响应。"""
    try:
        # 步骤 1: 从源读取Excel (路径或内存中的字节流)
        df = pd.read_excel(excel_source, engine='openpyxl')
        
        column_names = df.columns.tolist()
        if len(column_names) < 5:
            return schemas.GeneralResponse(status="error", message=f"错误：Excel文件必须至少包含5列。检测到 {len(column_names)} 列。")

        date_col, full_prof_col, cs_complaint_col, cs_fault_col, ps_prof_col = column_names[:5]

        # 步骤 2: 高效地清空旧数据
        # 使用 synchronize_session=False 来优化批量删除性能
        num_deleted_schedules = db.query(models.DutySchedule).delete(synchronize_session=False)
        num_deleted_logs = db.query(models.SwapLog).delete(synchronize_session=False)

        # 步骤 3: 使用快速、向量化的操作处理DataFrame
        # 3.1: 移除日期为空的行
        df.dropna(subset=[date_col], inplace=True)
        
        # 3.2: 将日期列转换为Python的date对象
        df[date_col] = pd.to_datetime(df[date_col]).dt.date

        # 3.3: 使用快速的列表推导式配合 to_dict('records') 替代慢速的 iterrows()
        records_to_insert = [
            models.DutySchedule(
                duty_date=row[date_col],
                employee_full_professional=row.get(full_prof_col),
                employee_cs_complaint=row.get(cs_complaint_col),
                employee_cs_fault=row.get(cs_fault_col),
                employee_ps_professional=row.get(ps_prof_col)
            ) for row in df.to_dict('records')
        ]
        
        # 步骤 4: 批量插入并提交
        db.add_all(records_to_insert)
        db.commit()
        return schemas.GeneralResponse(
            status="success",
            message=f"成功！清除了 {num_deleted_schedules} 条旧排班记录和 {num_deleted_logs} 条旧换班日志，并成功导入了 {len(records_to_insert)} 条新值班记录。"
        )
    except Exception as e:
        db.rollback()
        return schemas.GeneralResponse(status="error", message=f"处理Excel并存入数据库时发生错误: {e}")

def import_schedule(db: Session, file_path: str = None, file_content_b64: str = None) -> schemas.GeneralResponse:
    """统一的智能导入函数，返回结构化响应。"""
    if file_content_b64:
        try:
            # 解码 base64 内容
            decoded_content = base64.b64decode(file_content_b64)
            # 使用内存中的 BytesIO 对象，避免磁盘I/O
            excel_source = io.BytesIO(decoded_content)
            return _read_and_process_excel(db, excel_source)
        except Exception as e:
            return schemas.GeneralResponse(status="error", message=f"处理上传的文件内容时出错: {e}")
    elif file_path:
        cleaned_path = _normalize_path(file_path)
        if not os.path.exists(cleaned_path):
            return schemas.GeneralResponse(status="error", message=f"错误：文件路径不存在。解析后的路径为 '{cleaned_path}' (原始输入: '{file_path}')。")
        return _read_and_process_excel(db, cleaned_path)
    else:
        return schemas.GeneralResponse(status="error", message="错误：必须提供文件路径(file_path)或文件内容(file_content_b64)之一。")

def get_duty_employee(db: Session, duty_date_str: str) -> schemas.GetDutyEmployeeResponse:
    """查询指定日期的值班人员，返回结构化响应并集成智能提醒。"""
    if db.query(models.DutySchedule).first() is None:
        return schemas.GetDutyEmployeeResponse(status="error", message="数据库为空，请先使用`import_schedule`工具导入值班表。")

    try:
        is_today_query = duty_date_str.lower() == "today"
        if is_today_query:
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(duty_date_str, "%Y-%m-%d").date()
    except ValueError:
        return schemas.GetDutyEmployeeResponse(status="error", message=f"日期格式错误。请输入 'YYYY-MM-DD' 格式或 'today'。")

    schedule = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == target_date).first()
    
    if not schedule:
        return schemas.GetDutyEmployeeResponse(
            status="not_found",
            message=f"未找到 {target_date.strftime('%Y年%m月%d日')} 的值班记录。",
            duty_date=target_date
        )

    schedule_data = schemas.DutyEmployee(
        full_professional=schedule.employee_full_professional,
        cs_complaint=schedule.employee_cs_complaint,
        cs_fault=schedule.employee_cs_fault,
        ps_professional=schedule.employee_ps_professional
    )
    
    warnings = []
    if is_today_query:
        latest_date = db.query(func.max(models.DutySchedule.duty_date)).scalar()
        if latest_date and latest_date == target_date:
            warnings.append("提醒：这已经是排班表的最后一天，请记得及时导入新的排班表。")

    return schemas.GetDutyEmployeeResponse(
        status="success",
        message=f"{target_date.strftime('%Y年%m月%d日')} 的值班安排已找到。",
        duty_date=target_date,
        schedule=schedule_data,
        warnings=warnings
    )

def _find_employee_role(schedule: models.DutySchedule, employee_name: str) -> Optional[str]:
    """在一个排班记录中查找指定员工，并返回其角色字段名。"""
    found_roles = []
    for field, role in FIELD_TO_ROLE_MAP.items():
        if getattr(schedule, field) == employee_name:
            found_roles.append(field)
    
    if len(found_roles) == 1:
        return found_roles[0]
    # 如果找到0个或多个角色，则返回一个列表（或None），由调用者处理
    return found_roles if found_roles else None


def swap_duty_schedule(db: Session, request: schemas.SwapDutyScheduleByEmployeeRequest) -> schemas.SwapDutyScheduleResponse:
    """
    通过员工姓名，精准对调两个日期的值班人员。
    这是一个事务性操作，包含查找、对调和记录日志。
    """
    swap_info_1 = request.swap_info_1
    swap_info_2 = request.swap_info_2

    try:
        d1 = datetime.strptime(swap_info_1.duty_date, "%Y-%m-%d").date()
        d2 = datetime.strptime(swap_info_2.duty_date, "%Y-%m-%d").date()
    except ValueError:
        return schemas.SwapDutyScheduleResponse(status="error", message="日期格式错误，请输入 'YYYY-MM-DD' 格式。")

    schedule1 = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == d1).first()
    schedule2 = db.query(models.DutySchedule).filter(models.DutySchedule.duty_date == d2).first()

    if not schedule1 or not schedule2:
        missing_dates = []
        if not schedule1: missing_dates.append(swap_info_1.duty_date)
        if not schedule2: missing_dates.append(swap_info_2.duty_date)
        return schemas.SwapDutyScheduleResponse(status="error", message=f"错误：未找到以下一个或多个日期的排班记录: {', '.join(missing_dates)}")

    # 查找员工1的角色
    role_field1 = _find_employee_role(schedule1, swap_info_1.employee_name)
    if not isinstance(role_field1, str):
        if not role_field1:
            return schemas.SwapDutyScheduleResponse(status="error", message=f"错误：在 {swap_info_1.duty_date} 的排班中未找到员工 '{swap_info_1.employee_name}'。")
        else:
            return schemas.SwapDutyScheduleResponse(status="error", message=f"错误：员工 '{swap_info_1.employee_name}' 在 {swap_info_1.duty_date} 有多个排班，无法明确指定换班对象。")

    # 查找员工2的角色
    role_field2 = _find_employee_role(schedule2, swap_info_2.employee_name)
    if not isinstance(role_field2, str):
        if not role_field2:
            return schemas.SwapDutyScheduleResponse(status="error", message=f"错误：在 {swap_info_2.duty_date} 的排班中未找到员工 '{swap_info_2.employee_name}'。")
        else:
            return schemas.SwapDutyScheduleResponse(status="error", message=f"错误：员工 '{swap_info_2.employee_name}' 在 {swap_info_2.duty_date} 有多个排班，无法明确指定换班对象。")

    # 执行交换
    setattr(schedule1, role_field1, swap_info_2.employee_name)
    setattr(schedule2, role_field2, swap_info_1.employee_name)

    # 创建审计日志
    role1 = FIELD_TO_ROLE_MAP[role_field1]
    role2 = FIELD_TO_ROLE_MAP[role_field2]
    new_log = models.SwapLog(
        date1=d1, role1=role1, original_employee1=swap_info_1.employee_name, new_employee1=swap_info_2.employee_name,
        date2=d2, role2=role2, original_employee2=swap_info_2.employee_name, new_employee2=swap_info_1.employee_name
    )
    db.add(new_log)

    try:
        db.commit()
        
        swap1_details = schemas.SwapInfo(
            duty_date=d1, role=role1, original_employee=swap_info_1.employee_name, new_employee=swap_info_2.employee_name
        )
        swap2_details = schemas.SwapInfo(
            duty_date=d2, role=role2, original_employee=swap_info_2.employee_name, new_employee=swap_info_1.employee_name
        )
        
        return schemas.SwapDutyScheduleResponse(
            status="success",
            message=f"成功将 {swap_info_1.duty_date} 的 '{swap_info_1.employee_name}' ({role1}) 与 {swap_info_2.duty_date} 的 '{swap_info_2.employee_name}' ({role2}) 进行了对调。",
            swap1=swap1_details,
            swap2=swap2_details
        )
    except Exception as e:
        db.rollback()
        return schemas.SwapDutyScheduleResponse(status="error", message=f"数据库提交时发生错误: {e}")


def get_swap_logs(db: Session) -> schemas.GetSwapLogsResponse:
    """获取当前数据版本下所有的换班审计日志。"""
    try:
        logs_orm = db.query(models.SwapLog).order_by(models.SwapLog.log_time.desc()).all()
        log_count = len(logs_orm)
        
        # 将ORM对象格式化为人类可读的字符串
        formatted_logs = []
        for log in logs_orm:
            log_time_str = log.log_time.strftime("%Y-%m-%d %H:%M:%S")
            log_sentence = (
                f"[{log_time_str}] 换班申请: "
                f"{log.date1.strftime('%Y年%m月%d日')}的 '{log.original_employee1}' (原{log.role1}) "
                f"与 {log.date2.strftime('%Y年%m月%d日')}的 '{log.original_employee2}' (原{log.role2}) "
                f"进行了对调。"
            )
            formatted_logs.append(log_sentence)

        return schemas.GetSwapLogsResponse(
            status="success",
            message=f"成功查询到 {log_count} 条换班日志。",
            log_count=log_count,
            logs=formatted_logs
        )
    except Exception as e:
        return schemas.GetSwapLogsResponse(
            status="error",
            message=f"查询换班日志时发生错误: {e}",
            logs=[]
        )
