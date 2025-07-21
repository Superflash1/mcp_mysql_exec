from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# =================================================================
#                 通用响应模型 (Generic Responses)
# =================================================================

class GeneralResponse(BaseModel):
    """一个通用的响应模型，包含状态和消息，用于简单的操作结果。"""
    status: str = Field(..., description="操作结果状态，如 'success' 或 'error'")
    message: str = Field(..., description="给用户的可读消息")
    warnings: List[str] = Field([], description="操作过程中产生的警告信息列表")

# =================================================================
#             工具: import_schedule 的请求模型
# =================================================================

class ImportFromPathRequest(BaseModel):
    """通过路径导入文件的请求体模型。"""
    file_path: str = Field(..., description="服务器上Excel文件的绝对路径。")

# =================================================================
#             工具: get_duty_employee 的响应模型
# =================================================================

class DutyEmployee(BaseModel):
    """单个值班人员的信息。"""
    full_professional: Optional[str] = Field(None, description="全专业值班")
    cs_complaint: Optional[str] = Field(None, description="CS专业投诉值班")
    cs_fault: Optional[str] = Field(None, description="CS专业故障值班")
    ps_professional: Optional[str] = Field(None, description="PS专业值班")

class GetDutyEmployeeResponse(GeneralResponse):
    """查询值班人员的详细响应模型。"""
    duty_date: Optional[date] = Field(None, description="查询的值班日期")
    schedule: Optional[DutyEmployee] = Field(None, description="当天的值班安排详情")

# =================================================================
#             工具: swap_duty_schedule 的响应模型
# =================================================================

class SwapByEmployeeInfo(BaseModel):
    """换班请求中，单个换班单元的信息"""
    duty_date: str = Field(..., description="要换班的日期 (YYYY-MM-DD)")
    employee_name: str = Field(..., description="要换班的人员姓名")

class SwapDutyScheduleByEmployeeRequest(BaseModel):
    """通过员工姓名换班的请求体模型。"""
    swap_info_1: SwapByEmployeeInfo = Field(..., description="第一个换班人员的信息")
    swap_info_2: SwapByEmployeeInfo = Field(..., description="第二个换班人员的信息")

class SwapInfo(BaseModel):
    """描述一次对调操作的细节。"""
    duty_date: date = Field(..., description="对调的日期")
    role: str = Field(..., description="对调的专业名称")
    original_employee: Optional[str] = Field(None, description="原值班人员")
    new_employee: Optional[str] = Field(None, description="新值班人员")

class SwapDutyScheduleResponse(GeneralResponse):
    """换班操作的详细响应模型。"""
    swap1: Optional[SwapInfo] = Field(None, description="第一次对调的详情")
    swap2: Optional[SwapInfo] = Field(None, description="第二次对调的详情")

# =================================================================
#                 根路径欢迎页模型
# =================================================================

class WelcomeMessage(BaseModel):
    """根路径的欢迎信息。"""
    message: str
    documentation_url: str

# =================================================================
#                 换班审计日志模型
# =================================================================

class GetSwapLogsResponse(GeneralResponse):
    """获取换班日志列表的响应模型。"""
    log_count: int = Field(0, description="返回的日志条数")
    logs: List[str] = Field([], description="格式化为人类可读字符串的换班日志列表。") 