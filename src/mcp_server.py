"""
值班表管理MCP服务器
一个用于管理和查询Excel值班表的智能MCP服务，支持远程HTTP调用。

使用方法:
python src/mcp_server.py
"""

import base64
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context
from sqlalchemy.orm import Session

import sys
import os

# 添加项目根目录到Python路径，以便正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以正确导入模块
from src import services, schemas, models
from src.database import get_db, engine

# 应用状态管理
class AppState:
    def __init__(self):
        self.db_session = None

app_state = AppState()

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    """管理应用生命周期"""
    print("正在初始化数据库...")
    models.Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")
    
    try:
        yield app_state
    finally:
        print("MCP服务器正在关闭...")

# 创建MCP服务器实例
mcp = FastMCP(
    name="值班表管理MCP服务器",
    lifespan=lifespan
)

def get_db_session() -> Session:
    """获取数据库会话"""
    return next(get_db())

@mcp.tool()
def import_schedule_upload(
    file_content_b64: str,
    ctx: Context
) -> schemas.GeneralResponse:
    """
    通过Base64编码的文件内容智能导入值班表。此操作会覆盖所有旧数据。
    
    Args:
        file_content_b64: Base64编码的Excel文件内容
    
    Returns:
        包含操作结果的响应对象
    """
    try:
        db = get_db_session()
        result = services.import_schedule(db, file_content_b64=file_content_b64)
        db.close()
        return result
    except Exception as e:
        return schemas.GeneralResponse(
            status="error",
            message=f"导入失败: {str(e)}"
        )

@mcp.tool()
def import_schedule_path(
    file_path: str,
    ctx: Context
) -> schemas.GeneralResponse:
    """
    通过服务器本地路径智能导入值班表。此操作会覆盖所有旧数据。
    
    Args:
        file_path: 服务器上Excel文件的绝对路径
    
    Returns:
        包含操作结果的响应对象
    """
    try:
        db = get_db_session()
        result = services.import_schedule(db, file_path=file_path)
        db.close()
        return result
    except Exception as e:
        return schemas.GeneralResponse(
            status="error",
            message=f"导入失败: {str(e)}"
        )

@mcp.tool()
def get_duty_employee(
    ctx: Context,
    duty_date: str = "today"
) -> schemas.GetDutyEmployeeResponse:
    """
    查询指定日期的值班安排。
    
    Args:
        duty_date: 查询日期，格式为 "YYYY-MM-DD"，或直接使用 "today" 查询当天
    
    Returns:
        包含值班安排详情的响应对象
    """
    try:
        db = get_db_session()
        result = services.get_duty_employee(db, duty_date_str=duty_date)
        db.close()
        return result
    except Exception as e:
        db = get_db_session()
        db.close()
        return schemas.GetDutyEmployeeResponse(
            status="error",
            message=f"查询失败: {str(e)}"
        )

@mcp.tool()
def swap_duty_schedule(
    employee1_date: str,
    employee1_name: str,
    employee2_date: str,
    employee2_name: str,
    ctx: Context
) -> schemas.SwapDutyScheduleResponse:
    """
    通过员工姓名精准对调两个日期的值班人员。
    
    Args:
        employee1_date: 第一个员工的值班日期 (YYYY-MM-DD)
        employee1_name: 第一个员工的姓名
        employee2_date: 第二个员工的值班日期 (YYYY-MM-DD)
        employee2_name: 第二个员工的姓名
    
    Returns:
        包含换班操作详情的响应对象
    """
    try:
        db = get_db_session()
        
        # 构造请求对象
        request = schemas.SwapDutyScheduleByEmployeeRequest(
            swap_info_1=schemas.SwapByEmployeeInfo(
                duty_date=employee1_date,
                employee_name=employee1_name
            ),
            swap_info_2=schemas.SwapByEmployeeInfo(
                duty_date=employee2_date,
                employee_name=employee2_name
            )
        )
        
        result = services.swap_duty_schedule(db, request=request)
        db.close()
        return result
    except Exception as e:
        db = get_db_session()
        db.close()
        return schemas.SwapDutyScheduleResponse(
            status="error",
            message=f"换班失败: {str(e)}"
        )

@mcp.tool()
def get_swap_logs(ctx: Context) -> schemas.GetSwapLogsResponse:
    """
    查询当前数据版本下，所有的换班操作审计日志。
    日志会按时间倒序排列，最新的记录在最前面。
    
    Returns:
        包含换班日志列表的响应对象
    """
    try:
        db = get_db_session()
        result = services.get_swap_logs(db)
        db.close()
        return result
    except Exception as e:
        db = get_db_session()
        db.close()
        return schemas.GetSwapLogsResponse(
            status="error",
            message=f"查询日志失败: {str(e)}"
        )

@mcp.tool()
async def get_server_info(ctx: Context) -> dict:
    """
    获取MCP服务器信息和使用帮助。
    
    Returns:
        服务器信息和工具说明
    """
    return {
        "server_name": "值班表管理MCP服务器",
        "version": "2.0.0",
        "description": "一个用于管理和查询Excel值班表的智能MCP服务",
        "available_tools": [
            {
                "name": "import_schedule_upload",
                "description": "通过Base64文件内容导入排班表"
            },
            {
                "name": "import_schedule_path", 
                "description": "通过文件路径导入排班表"
            },
            {
                "name": "get_duty_employee",
                "description": "查询指定日期的值班人员"
            },
            {
                "name": "swap_duty_schedule",
                "description": "交换两个员工的值班安排"
            },
            {
                "name": "get_swap_logs",
                "description": "查询换班操作日志"
            }
        ],
        "transport": "streamable-http",
        "endpoint": "http://localhost:8000/mcp"
    }

def main():
    """启动MCP服务器"""
    print("="*60)
    print("正在启动值班表管理MCP服务器...")
    print("传输方式: stdio (标准输入输出)")
    print("="*60)
    print("服务器启动后可通过MCP客户端连接使用")
    print("支持的工具:")
    print("  - import_schedule_upload: 导入排班表(Base64)")
    print("  - import_schedule_path: 导入排班表(文件路径)")
    print("  - get_duty_employee: 查询值班人员")
    print("  - swap_duty_schedule: 交换值班安排")
    print("  - get_swap_logs: 查询换班日志")
    print("="*60)
    
    # 使用默认的stdio传输方式，这是最兼容的方式
    mcp.run()

if __name__ == "__main__":
    main() 