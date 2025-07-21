# 实战教程：如何从零开始构建一个健壮的MCP服务器
**（以“值班表管理”项目为例）**

## 1. 前言：为什么要用这个开发框架？

在开发任何服务时，我们通常会面临两类问题：
1.  **通用技术问题**: 如何搭建Web服务？如何连接数据库？如何保证API接口的数据格式正确？如何管理配置信息？如何保证安全性？
2.  **核心业务问题**: 就本项目而言，即如何解析Excel？如何实现换班逻辑？如何查询特定日期的值班人员？

传统的开发方式常常将这两类问题混杂在一起，导致代码难以维护和扩展。

本教程提出的**分层开发框架**，旨在将上述两类问题彻底分离。我们将构建一个坚实可靠的“技术底座”，让您在开发时，几乎只需要关心**核心业务问题**。您可以将90%的精力投入到`src/services.py`这个文件中，实现您真正想解决的业务逻辑。

**本框架将为您自动处理：**
*   高性能的Web API服务 (基于FastAPI)。
*   数据库的自动创建与连接管理 (基于SQLAlchemy)。
*   API输入输出数据的严格校验与自动文档生成 (基于Pydantic)。
*   安全、灵活的配置管理 (基于`.env`文件)。

---

## 2. 最终架构：我们的目标

在开始之前，我们先明确我们最终要构建的项目是什么样子。这是一个典型的分层架构：

```
mcp_project/
├── project_document/       # (本项目所有文档)
├── src/                    # 源代码核心目录
│   ├── config.py           # 负责加载.env配置 (技术底层)
│   ├── database.py         # 数据库连接与初始化 (技术底层)
│   ├── models.py           # 数据库表结构定义 (业务相关)
│   ├── schemas.py          # API数据格式定义 (业务相关)
│   ├── services.py         # **核心业务逻辑 (您最需要关注的文件)**
│   └── main.py             # Web API入口与路由 (技术底层)
├── .env.example            # 环境变量模板
└── requirements.txt        # Python依赖列表
```

*   **技术底层**: `config.py`, `database.py`, `main.py`。这些文件构成了框架的核心，通常一次配置完成，后续很少改动。
*   **业务相关**: `models.py`, `schemas.py`, `services.py`。这三个文件与您的具体业务逻辑紧密相关，是您开发新功能时主要打交道的地方。

---

## 3. Phase 1: 环境搭建与配置 (一次性工作)

这是项目的“地基”，通常在项目开始时一次性完成。

#### **步骤1: 建立项目结构**
按照上一节的结构，创建对应的目录和空的`.py`文件。

#### **步骤2: 定义环境依赖 (`requirements.txt`)**
这是我们框架所需的所有“轮子”。
```txt
# requirements.txt
fastapi
uvicorn[standard]
python-multipart
pandas
openpyxl
SQLAlchemy
mysql-connector-python
python-dotenv
```

#### **步骤3: 定义配置文件模板 (`.env.example`)**
将所有需要随环境变化的配置（尤其是密码等敏感信息）都放在这里。
```dotenv
# .env.example
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=your_db_name
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
```
**实践要点**: 实际部署时，应复制此文件为`.env`并填写真实信息。`.env`文件**绝不能**提交到Git等版本控制系统中。

---

## 4. Phase 2: 实现技术底层 (框架核心)

现在，我们来实现那些“一次编写，到处使用”的框架文件。

#### **文件1: `src/config.py` - 配置加载器**
它的唯一职责就是读取`.env`文件，并将其内容暴露给程序的其他部分。
```python
# src/config.py
import os
from dotenv import load_dotenv

# 从.env文件加载环境变量
# 加上 encoding="gbk" 是为了兼容在中文Windows环境下创建的.env文件
load_dotenv(encoding="gbk")

# 从环境变量中读取配置，如果不存在则使用默认值
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# 构建SQLAlchemy所需的数据库连接URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
```

#### **文件2: `src/database.py` - 数据库管理器**
这是框架的亮点之一。它不仅管理数据库连接，还能在服务启动时**自动创建数据库**。
```python
# src/database.py
import mysql.connector
from mysql.connector import errorcode
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 从我们的配置模块导入信息
from .config import DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE, DATABASE_URL

def ensure_database_exists():
    """在程序启动时，确保目标数据库存在，如果不存在则自动创建。"""
    try:
        # 先不带数据库名进行连接
        cnx = mysql.connector.connect(user=DB_USERNAME, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cursor = cnx.cursor()
        
        # 尝试创建数据库
        try:
            cursor.execute(f"CREATE DATABASE {DB_DATABASE} DEFAULT CHARACTER SET 'utf8mb4'")
        except mysql.connector.Error as err:
            if err.errno != errorcode.ER_DB_CREATE_EXISTS: # 如果不是“数据库已存在”的错误，则抛出
                raise err
        
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        print(f"数据库连接或创建失败: {err}")
        exit(1) # 如果失败，则终止程序

# --- 初始化流程 ---
ensure_database_exists()  # 执行检查
engine = create_engine(DATABASE_URL) # 创建SQLAlchemy引擎
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() # 所有数据库模型的基类

# 数据库会话依赖，FastAPI将用它来为每个请求提供独立的数据库连接
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### **文件3: `src/main.py` - API服务器**
这是连接“外部世界”和“内部逻辑”的桥梁。
```python
# src/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import services, schemas, models
from .database import get_db, engine

# --- 初始化 ---
# 在应用启动时，根据models.py中的定义，自动创建所有数据表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的MCP服务器")

# --- API路由定义 ---

# 最佳实践1：为不同输入类型的同一功能，创建独立的API。
# 这比用一个复杂的、带可选参数的API更健壮。
@app.post("/import_schedule/path", response_model=schemas.GeneralResponse, tags=["数据管理"])
def import_from_path(
    request: schemas.ImportFromPathRequest,
    db: Session = Depends(get_db)
):
    """通过服务器本地路径导入排班表。"""
    return services.import_schedule(db, file_path=request.file_path)

# 最佳实践2：对于需要复杂输入的业务逻辑，定义专门的请求体。
@app.post("/swap_duty_by_name/", response_model=schemas.SwapDutyScheduleResponse, tags=["核心功能"])
def swap_by_name(
    request: schemas.SwapDutyScheduleByEmployeeRequest,
    db: Session = Depends(get_db)
):
    """通过员工姓名执行换班。"""
    return services.swap_duty_schedule(db, request=request)


@app.get("/get_duty_employee/", response_model=schemas.GetDutyEmployeeResponse, tags=["查询"])
def get_duty_employee_endpoint(
    duty_date: str = "today",
    db: Session = Depends(get_db) # FastAPI会自动注入数据库会话
):
    # 直接调用核心业务函数，并返回其结果
    return services.get_duty_employee(db, duty_date_str=duty_date)

# ... 在这里为您在services.py中创建的每个功能都添加一个类似的端点 ...

# --- 启动命令 ---
# 可以通过在终端运行 `python -m src.main` 来启动这个服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

至此，我们的“技术底座”已经搭建完毕！现在进入最关键的部分。

---

## 5. Phase 3: 实现核心业务 (您的主战场)

开发新功能时，您通常只需要按以下“三步曲”操作：

#### **第1步: 定义数据表结构 (`src/models.py`)**
您需要什么样的数据表？就在这里定义。
```python
# src/models.py
from sqlalchemy import Column, Integer, String, Date
from .database import Base # 继承我们创建的基类

class DutySchedule(Base):
    __tablename__ = "duty_schedules" # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)
    duty_date = Column(Date, unique=True, nullable=False)
    
    # 根据您的业务需求定义字段
    employee_full_professional = Column(String(255))
    employee_cs_complaint = Column(String(255))
    # ...
```

#### **第2步: 定义API数据格式 (`src/schemas.py`)**
您的API要接收和返回什么样的数据？用Pydantic在这里定义，可以获得免费的数据校验和文档。
```python
# src/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import date

# 定义一个通用的响应体，让所有API返回格式统一
class GeneralResponse(BaseModel):
    status: str
    message: str

# 为get_duty_employee的返回数据定义一个精确的格式
class DutyEmployee(BaseModel):
    full_professional: Optional[str]
    cs_complaint: Optional[str]
    # ...

class GetDutyEmployeeResponse(GeneralResponse):
    duty_date: Optional[date]
    schedule: Optional[DutyEmployee]

# 为“按姓名换班”功能定义更复杂的请求和响应模型
class SwapByEmployeeInfo(BaseModel):
    duty_date: str
    employee_name: str

class SwapDutyScheduleByEmployeeRequest(BaseModel):
    swap_info_1: SwapByEmployeeInfo
    swap_info_2: SwapByEmployeeInfo

class SwapInfo(BaseModel):
    duty_date: date
    role: str
    original_employee: Optional[str]
    new_employee: Optional[str]

class SwapDutyScheduleResponse(GeneralResponse):
    swap1: Optional[SwapInfo]
    swap2: Optional[SwapInfo]
```

#### **第3rd步: 编写业务逻辑 (`src/services.py`)**
**这是您施展才华的地方！** `config`, `database`已经为您铺好了路，`models`和`schemas`是您的工具，在这里实现功能的具体逻辑。

以`swap_duty_schedule`为例，展示一个更复杂的业务流程：
```python
# src/services.py
from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas # 导入您的工具

def _find_employee_role(schedule: models.DutySchedule, name: str) -> list:
    """内部辅助函数：在排班记录中查找一个员工可能担任的所有角色。"""
    # (这里是查找逻辑) ...
    pass

def swap_duty_schedule(db: Session, request: schemas.SwapDutyScheduleByEmployeeRequest) -> schemas.SwapDutyScheduleResponse:
    """这是核心业务逻辑函数，按姓名换班"""

    # 1. 解析输入
    swap1_info = request.swap_info_1
    swap2_info = request.swap_info_2
    
    # 2. 从数据库查询相关记录
    schedule1 = db.query(models.DutySchedule).filter_by(duty_date=swap1_info.duty_date).first()
    schedule2 = db.query(models.DutySchedule).filter_by(duty_date=swap2_info.duty_date).first()
    if not (schedule1 and schedule2):
        return schemas.SwapDutyScheduleResponse(status="error", message="日期记录未找到。")

    # 3. 执行核心业务逻辑判断 (这是关键！)
    # 先查找员工1的角色，并处理找不到或找到多个的歧义情况
    role1 = _find_employee_role(schedule1, swap1_info.employee_name)
    if len(role1) != 1:
        return schemas.SwapDutyScheduleResponse(status="error", message=f"无法明确 {swap1_info.employee_name} 的角色。")
    
    # 查找员工2的角色...
    role2 = _find_employee_role(schedule2, swap2_info.employee_name)
    if len(role2) != 1:
        return schemas.SwapDutyScheduleResponse(status="error", message=f"无法明确 {swap2_info.employee_name} 的角色。")

    # 4. 执行数据库操作
    # (这里是更新数据库的代码) ...
    # db.commit()

    # 5. 格式化输出，返回结构化的成功响应
    response_details1 = schemas.SwapInfo(...)
    response_details2 = schemas.SwapInfo(...)
    
    return schemas.SwapDutyScheduleResponse(
        status="success",
        message="换班成功！",
        swap1=response_details1,
        swap2=response_details2
    )
```

**每当您要添加一个新功能，例如“添加员工”：**
1.  **`models.py`**: 可能需要一个`Employee`模型。
2.  **`schemas.py`**: 定义一个`CreateEmployeeRequest`和`EmployeeResponse`。
3.  **`services.py`**: 创建一个`create_employee`函数，它接收`db`和`CreateEmployeeRequest`，操作数据库，然后返回`EmployeeResponse`。
4.  **`main.py`**: 添加一个`@app.post("/create_employee/")`端点，将请求转发给`services.create_employee`函数。

流程清晰，职责分明。

---

## 6. 新功能开发工作流总结

当您已经完成了上述框架的搭建，需要为您的MCP服务器添加一个**新功能**时，您只需要遵循以下清晰的“四步曲”。这个流程能确保您的代码结构清晰、逻辑分离、易于维护。

### **第一步：思考数据存储 - `models.py`**

*   **任务**: 定义您的数据在数据库中如何存储。
*   **动作**:
    1.  打开 `src/models.py`。
    2.  思考新功能是否需要新的数据表。
    3.  如果需要，就创建一个新的 class，继承自 `database.Base`，并使用 SQLAlchemy 的 `Column` 定义表的字段。
    *   *如果新功能只是操作现有数据，则可以跳过此步。*

### **第二步：思考API契约 - `schemas.py`**

*   **任务**: 定义您的API如何与外部世界“对话”。
*   **动作**:
    1.  打开 `src/schemas.py`。
    2.  **定义请求体**: 如果API需要接收复杂JSON数据（如我们的“按姓名换班”），就创建一个继承自`pydantic.BaseModel`的`Request`类。
    3.  **定义响应体**: 为API创建一个`Response`类，明确地告诉调用者成功或失败时会返回什么样的数据结构。这对于构建可预测、易于调试的系统至关重要。

### **第三步：实现核心逻辑 - `services.py`**

*   **任务**: **这是您的主战场**。在这里编写功能的实际业务逻辑，处理所有边界情况和错误，完全不用关心Web请求、数据库连接等细节。
*   **动作**:
    1.  打开 `src/services.py`。
    2.  创建一个新的Python函数。
    3.  此函数的参数通常是 `db: Session` 和一个您在 `schemas.py` 中定义的请求模型。
    4.  在函数内部，使用 `db` 对象和您在 `models.py` 中定义的ORM模型来执行数据库的增、删、改、查。
    5.  执行所有业务计算和逻辑判断。
    6.  最后，将结果包装成您在 `schemas.py` 中定义的响应模型并 `return`。

### **第四步：暴露API端点 - `main.py`**

*   **任务**: 将您刚刚编写的业务逻辑函数，通过一个URL暴露给外部世界。
*   **动作**:
    1.  打开 `src/main.py`。
    2.  使用FastAPI的装饰器（如 `@app.post("/your-new-feature")` 或 `@app.get(...)`）创建一个新的API端点函数。
    3.  在这个函数里，调用您在 `services.py` 中创建的核心逻辑函数。
    4.  将函数的返回值直接 `return`。FastAPI会利用您在 `schemas.py` 中的定义，自动完成数据序列化。

遵循这四步，您就可以不断地为您的MCP服务器添加新的、健壮的功能，同时保持代码库的整洁和专业。 

---

## 7. 总结

这个框架通过“约定优于配置”的原则，为您处理了大部分重复性、技术性的底层工作。它强制实行了良好的软件工程实践（如分层、依赖注入、数据校验），使您能够更快速、更安全、更愉快地进行MCP服务器的业务功能开发。

希望这份从我们合作中提炼出的教程，能成为您未来项目的得力助手！