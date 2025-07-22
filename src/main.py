from fastapi import FastAPI, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import typing
import uvicorn
import base64

from . import services, schemas, models
from .database import get_db, engine

# --- 数据库与应用初始化 ---
# 修复BUG：在应用启动时，确保所有定义的表都被创建
# 这行代码应该在定义了所有模型之后，但在应用开始接收请求之前执行。
print("正在检查并创建数据库表...")
models.Base.metadata.create_all(bind=engine)
print("数据库表检查完成。")


# --- FastAPI应用实例 ---
app = FastAPI(
    title="值班表管理MCP",
    description="一个用于管理和查询Excel值班表的智能MCP服务，带Web API接口。",
    version="2.0.0",
)

@app.get("/", response_model=schemas.WelcomeMessage, tags=["概览"])
def read_root():
    """
    根路径，提供服务的欢迎信息和文档链接。
    """
    return {
        "message": "欢迎使用值班表管理MCP API!",
        "documentation_url": "/docs"
    }


# --- MCP 工具定义 (同时也是API端点) ---

@app.post("/import_schedule/upload", response_model=schemas.GeneralResponse, tags=["数据管理"])
async def import_schedule_from_upload(
    file: UploadFile = File(..., description="上传的Excel文件"),
    db: Session = Depends(get_db)
) -> schemas.GeneralResponse:
    """
    通过**上传文件**智能导入值班表。此操作会覆盖所有旧数据。
    """
    content = await file.read()
    b64_content = base64.b64encode(content).decode('utf-8')
    return services.import_schedule(db, file_content_b64=b64_content)

@app.post("/import_schedule/path", response_model=schemas.GeneralResponse, tags=["数据管理"])
def import_schedule_from_path(
    request: schemas.ImportFromPathRequest,
    db: Session = Depends(get_db)
) -> schemas.GeneralResponse:
    """
    通过**服务器本地路径**智能导入值班表。此操作会覆盖所有旧数据。路径格式为：
    D:/code/mcp开发/mcp_mysql_exec/排班表.xlsx
    """
    return services.import_schedule(db, file_path=request.file_path)

@app.get("/get_duty_employee/", response_model=schemas.GetDutyEmployeeResponse, tags=["查询"])
def get_duty_employee(
    duty_date: str = "today",
    db: Session = Depends(get_db)
) -> schemas.GetDutyEmployeeResponse:
    """
    查询指定日期的值班安排。
    
    - **duty_date**: 查询日期，格式为 "YYYY-MM-DD"，或直接使用 "today" 查询当天。
    """
    return services.get_duty_employee(db, duty_date_str=duty_date)

@app.post("/swap_duty_schedule/", response_model=schemas.SwapDutyScheduleResponse, tags=["数据管理"])
def swap_duty_schedule(
    request: schemas.SwapDutyScheduleByEmployeeRequest,
    db: Session = Depends(get_db)
) -> schemas.SwapDutyScheduleResponse:
    """
    通过**员工姓名**精准对调两个日期的值班人员。

    在请求体中提供两个要对调的人员信息，每个信息包含日期和姓名。
    """
    return services.swap_duty_schedule(db, request=request)

@app.get("/get_swap_logs/", response_model=schemas.GetSwapLogsResponse, tags=["审计"])
def get_swap_logs(db: Session = Depends(get_db)) -> schemas.GetSwapLogsResponse:
    """
    查询当前数据版本下，所有的换班操作审计日志。
    日志会按时间倒序排列，最新的记录在最前面。
    """
    return services.get_swap_logs(db)


# --- 服务器启动逻辑 ---
if __name__ == "__main__":
    print("="*50)
    print("正在启动FastAPI服务器...")
    print("本地服务器部署时，交互式API文档将可在 http://127.0.0.1:8000/docs 查看")
    print("="*50)
    print("远程服务器部署时，交互式API文档将可在 http://<IP>:8000/docs 查看")
    uvicorn.run(app, host="0.0.0.0", port=8000)
