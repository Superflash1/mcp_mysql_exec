#!/usr/bin/env python3
"""
独立的值班表管理MCP服务器
专门用于Inspector测试，避免相对导入问题。

使用方法:
python mcp_server_standalone.py
"""

import asyncio
import sys
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from datetime import date

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from mcp.server.fastmcp import FastMCP, Context

# 简化的响应模型，避免复杂的依赖
class SimpleResponse:
    def __init__(self, status: str, message: str, data=None):
        self.status = status
        self.message = message
        self.data = data
    
    def dict(self):
        result = {"status": self.status, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result

# 应用状态管理
class AppState:
    def __init__(self):
        self.db_available = False

app_state = AppState()

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    """管理应用生命周期"""
    print("正在初始化MCP服务器...")
    
    # 尝试检查数据库连接
    try:
        import mysql.connector
        # 简化的数据库检查
        app_state.db_available = True
        print("数据库连接检查完成")
    except Exception as e:
        print(f"数据库不可用: {e}")
        app_state.db_available = False
    
    print("MCP服务器初始化完成")
    
    try:
        yield app_state
    finally:
        print("MCP服务器正在关闭...")

# 创建MCP服务器实例
mcp = FastMCP(
    name="值班表管理MCP服务器",
    lifespan=lifespan
)

@mcp.tool()
def import_schedule_upload(
    file_content_b64: str,
    ctx: Context
) -> dict:
    """
    通过Base64编码的文件内容智能导入值班表。此操作会覆盖所有旧数据。
    
    Args:
        file_content_b64: Base64编码的Excel文件内容
    
    Returns:
        包含操作结果的响应对象
    """
    try:
        # 简化的实现，只做基本验证
        if not file_content_b64:
            return {"status": "error", "message": "文件内容不能为空"}
        
        # 验证是否为有效的Base64
        import base64
        try:
            base64.b64decode(file_content_b64)
        except Exception:
            return {"status": "error", "message": "无效的Base64编码"}
        
        if app_state.db_available:
            return {"status": "success", "message": "排班表导入成功（模拟）", "warnings": ["这是测试模式"]}
        else:
            return {"status": "error", "message": "数据库不可用，无法导入"}
        
    except Exception as e:
        return {"status": "error", "message": f"导入失败: {str(e)}"}

@mcp.tool()
def import_schedule_path(
    file_path: str,
    ctx: Context
) -> dict:
    """
    通过服务器本地路径智能导入值班表。此操作会覆盖所有旧数据。
    
    Args:
        file_path: 服务器上Excel文件的绝对路径
    
    Returns:
        包含操作结果的响应对象
    """
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"文件不存在: {file_path}"}
        
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            return {"status": "error", "message": "文件格式必须是Excel (.xlsx或.xls)"}
        
        if app_state.db_available:
            return {"status": "success", "message": f"排班表从 {file_path} 导入成功（模拟）", "warnings": ["这是测试模式"]}
        else:
            return {"status": "error", "message": "数据库不可用，无法导入"}
        
    except Exception as e:
        return {"status": "error", "message": f"导入失败: {str(e)}"}

@mcp.tool()
def get_duty_employee(
    ctx: Context,
    duty_date: str = "today"
) -> dict:
    """
    查询指定日期的值班安排。
    
    Args:
        duty_date: 查询日期，格式为 "YYYY-MM-DD"，或直接使用 "today" 查询当天
    
    Returns:
        包含值班安排详情的响应对象
    """
    try:
        from datetime import datetime
        
        if duty_date == "today":
            query_date = datetime.now().strftime("%Y-%m-%d")
        else:
            # 验证日期格式
            try:
                datetime.strptime(duty_date, "%Y-%m-%d")
                query_date = duty_date
            except ValueError:
                return {"status": "error", "message": "日期格式错误，请使用 YYYY-MM-DD 格式"}
        
        if app_state.db_available:
            # 模拟查询结果
            return {
                "status": "success",
                "message": "查询成功",
                "duty_date": query_date,
                "schedule": {
                    "full_professional": "张三（模拟数据）",
                    "cs_complaint": "李四（模拟数据）",
                    "cs_fault": "王五（模拟数据）",
                    "ps_professional": "赵六（模拟数据）"
                },
                "warnings": ["这是测试模式，显示的是模拟数据"]
            }
        else:
            return {"status": "error", "message": "数据库不可用，无法查询"}
        
    except Exception as e:
        return {"status": "error", "message": f"查询失败: {str(e)}"}

@mcp.tool()
def swap_duty_schedule(
    employee1_date: str,
    employee1_name: str,
    employee2_date: str,
    employee2_name: str,
    ctx: Context
) -> dict:
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
        from datetime import datetime
        
        # 验证日期格式
        try:
            datetime.strptime(employee1_date, "%Y-%m-%d")
            datetime.strptime(employee2_date, "%Y-%m-%d")
        except ValueError:
            return {"status": "error", "message": "日期格式错误，请使用 YYYY-MM-DD 格式"}
        
        if not employee1_name or not employee2_name:
            return {"status": "error", "message": "员工姓名不能为空"}
        
        if app_state.db_available:
            # 模拟换班操作
            return {
                "status": "success",
                "message": "换班操作成功（模拟）",
                "swap1": {
                    "duty_date": employee1_date,
                    "role": "全专业值班（模拟）",
                    "original_employee": employee1_name,
                    "new_employee": employee2_name
                },
                "swap2": {
                    "duty_date": employee2_date,
                    "role": "全专业值班（模拟）",
                    "original_employee": employee2_name,
                    "new_employee": employee1_name
                },
                "warnings": ["这是测试模式，未实际执行换班操作"]
            }
        else:
            return {"status": "error", "message": "数据库不可用，无法执行换班操作"}
        
    except Exception as e:
        return {"status": "error", "message": f"换班失败: {str(e)}"}

@mcp.tool()
def get_swap_logs(ctx: Context) -> dict:
    """
    查询当前数据版本下，所有的换班操作审计日志。
    日志会按时间倒序排列，最新的记录在最前面。
    
    Returns:
        包含换班日志列表的响应对象
    """
    try:
        if app_state.db_available:
            # 模拟日志数据
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "status": "success",
                "message": "日志查询成功",
                "log_count": 2,
                "logs": [
                    f"[{current_time}] 张三与李四交换值班安排 (2024-12-20 <-> 2024-12-21) - 模拟数据",
                    f"[{current_time}] 王五与赵六交换值班安排 (2024-12-18 <-> 2024-12-19) - 模拟数据"
                ],
                "warnings": ["这是测试模式，显示的是模拟日志"]
            }
        else:
            return {
                "status": "success",
                "message": "日志查询成功",
                "log_count": 0,
                "logs": [],
                "warnings": ["数据库不可用，返回空日志"]
            }
        
    except Exception as e:
        return {"status": "error", "message": f"查询日志失败: {str(e)}"}

@mcp.tool()
async def get_server_info(ctx: Context) -> dict:
    """
    获取MCP服务器信息和使用帮助。
    
    Returns:
        服务器信息和工具说明
    """
    return {
        "server_name": "值班表管理MCP服务器",
        "version": "2.0.0-standalone",
        "description": "一个用于管理和查询Excel值班表的智能MCP服务（独立测试版本）",
        "database_status": "可用" if app_state.db_available else "不可用",
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
        "transport": "stdio",
        "note": "这是独立测试版本，用于MCP Inspector调试"
    }

def main():
    """启动MCP服务器"""
    print("="*60)
    print("正在启动值班表管理MCP服务器（独立版本）...")
    print("传输方式: stdio (标准输入输出)")
    print("="*60)
    print("服务器启动后可通过MCP客户端连接使用")
    print("支持的工具:")
    print("  - import_schedule_upload: 导入排班表(Base64)")
    print("  - import_schedule_path: 导入排班表(文件路径)")
    print("  - get_duty_employee: 查询值班人员")
    print("  - swap_duty_schedule: 交换值班安排")
    print("  - get_swap_logs: 查询换班日志")
    print("  - get_server_info: 获取服务器信息")
    print("="*60)
    
    # 使用默认的stdio传输方式
    mcp.run()

if __name__ == "__main__":
    main() 