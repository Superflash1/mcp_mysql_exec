# 最终版：技术实现与决策权威日志

**协议版本:** RIPER-5 v4.1
**项目代号:** mcp_mysql_exec
**AI助手:** Sun Wukong (AI)

---

## 第一阶段: 项目启动与协议确认

*   **用户指令:** 用户发起了项目，要求开发一个带详尽注释和文档的Python MCP Server。核心要求是必须遵循用户设定的高质量开发流程，并引入了`RIPER-5`协议。用户提出，应先创建需求文档，后续由用户增删改查。
*   **AI响应与动作 (RESEARCH模式):**
    *   **技术决策:** 确认遵循`RIPER-5`协议，采用结构化、文档驱动的开发模式。`project_document`目录被确立为项目的“唯一事实来源”，所有产出和决策都必须在此记录，确保可追溯性。
    *   **技术实现:**
        1.  通过 `mkdir project_document` 命令，创建了项目的基础目录结构。
        2.  创建核心任务文件 `project_document/mcp_mysql_exec_task.md`，并按照协议模板填充了初始框架。

---

## 第二阶段: 需求澄清与初步方案设计

*   **用户指令:** 用户提供了第一版核心需求：从Excel读取值班表，存入MySQL，并支持查询和修改（换班）。
*   **AI响应与动作 (RESEARCH -> INNOVATE模式):**
    *   **技术决策 (INNOVATE):** 对比了两种后端实现方案，这是项目第一个关键的技术抉择。
        1.  **方案A (轻量级/不推荐):** 使用 `mysql-connector-python` 手动编写原生SQL。
            *   *风险分析:* 换班操作可能需要这样的代码：`cursor.execute("UPDATE ... WHERE date = %s", (date1,)); cursor.execute("UPDATE ... WHERE date = %s", (date2,)); db.commit();`。这种方式不仅繁琐，而且如果字符串格式化稍有不慎，极易引入SQL注入漏洞。
        2.  **方案B (稳健型/推荐):** 使用 `SQLAlchemy` ORM (对象关系映射) + `Pandas`。
            *   *优势分析:* 换班操作的代码会变成：`schedule1.employee_name = name2; schedule2.employee_name = name1; db.commit();`。代码操作的是Python对象，而不是SQL字符串，由ORM库负责生成安全的SQL。**这从根本上杜绝了SQL注入风险**，且代码的可读性和可维护性远超方案A。
        *   **最终决定:** 基于“安全优先”和“长期可维护性”原则，**最终敲定了方案B**。
    *   **技术实现:** 在 `mcp_mysql_exec_task.md` 中更新了方案对比表格，并明确记录了推荐方案及其理由。

---

## 第三阶段: 详细规划与蓝图设计

*   **AI响应与动作 (PLAN模式):**
    *   **技术决策:** 将方案B具象化为详细的技术蓝图，不留模糊地带。
    *   **技术实现 (文档输出):** 在 `mcp_mysql_exec_task.md` 中，输出了项目的完整设计蓝图，其核心技术点如下：
        *   **项目文件结构规划:**
            ```
            mcp_mysql_exec/
            ├── src/
            │   ├── config.py         # 负责加载.env配置
            │   ├── database.py       # SQLAlchemy引擎和会话管理
            │   ├── models.py         # ORM模型定义 (最初为单人值班)
            │   ├── services.py       # 核心业务逻辑
            │   └── main.py           # MCP Server入口，定义工具
            ├── tests/              # 单元测试目录
            ...
            ```
        *   **初步数据库表设计 (后被迭代):**
            ```sql
            CREATE TABLE duty_schedules (
                id INT PRIMARY KEY AUTO_INCREMENT,
                duty_date DATE NOT NULL UNIQUE,
                employee_name VARCHAR(255) NOT NULL
            );
            ```
        *   **MCP工具接口定义:**
            *   `import_schedule_from_excel(file_path: str) -> str`
            *   `get_duty_employee(duty_date: str) -> str`
            *   `swap_duty_schedule(date1: str, date2: str) -> str`

---

## 第四阶段: 首次编码与三次关键迭代

*   **AI响应与动作 (EXECUTE -> RESEARCH -> EXECUTE模式):**
    1.  **初步编码 (EXECUTE):** AI严格按照Checklist，完成了项目骨架的搭建和所有基于“单人值班”模型的业务逻辑编码。此时，`models.py`和`services.py`的V1版本内容如下：
        *   `src/models.py` (V1 - 单人值班模型)
            ```python
            from sqlalchemy import Column, Integer, String, Date
            from .database import Base

            class DutySchedule(Base):
                __tablename__ = "duty_schedules"
                id = Column(Integer, primary_key=True)
                duty_date = Column(Date, unique=True, nullable=False)
                employee_name = Column(String(255), nullable=False)
            ```
        *   *此时的 `services.py` 包含了基于 `'日期'` 和 `'姓名'` 列名的三个核心功能。*

    2.  **用户反馈与迭代1 (数据探查与修正):**
        *   **用户指令:** 用户提供了真实的`排班表.xlsx`，要求根据此文件审视设计。
        *   **技术决策:** 放弃猜想，必须通过代码主动探查数据源的真实结构。
        *   **技术实现:**
            *   编写并执行了临时脚本 `inspect_excel.py`。
            *   **关键发现:** 脚本输出 `['日期            平常：9:00-17:30\n周末：9:00-17:30', '全专业值班', 'CS专业投诉值班', ...]`，证明了真实列名与原假设完全不同。
            *   **代码修正:** `src/services.py`中的`import_schedule_from_excel`函数被立刻修正，将硬编码的`'日期'`和`'姓名'`替换为探查到的真实列名，并暂定使用`'全专业值班'`作为主要值班列。

    3.  **用户反馈与迭代2 (升级为多角色查询):**
        *   **用户指令:** 用户明确指出，查询时需要返回**所有四个专业**的值班人员。
        *   **技术决策:** 识别为一次重要的数据库和业务逻辑重构，必须将“单人模型”升级为“多角色模型”。
        *   **技术实现 (重构):**
            *   **数据库模型 (`src/models.py`):** `employee_name`字段被移除，替换为四个独立的、可为空的专业值班字段。
                ```python
                class DutySchedule(Base):
                    # ...
                    employee_full_professional = Column(String(255), nullable=True)
                    employee_cs_complaint = Column(String(255), nullable=True)
                    employee_cs_fault = Column(String(255), nullable=True)
                    employee_ps_professional = Column(String(255), nullable=True)
                ```
            *   **查询逻辑 (`src/services.py`):** `get_duty_employee`函数的返回逻辑被重写，以生成一个格式化的多行字符串，清晰地列出所有角色的值班情况，并处理“无安排”的场景。
            *   **换班逻辑 (`src/services.py`):** `swap_duty_schedule`被初步升级为“整体对调”，即交换两个日期的所有四个字段。

    4.  **用户反馈与迭代3 (升级为精准换班):**
        *   **用户指令:** 用户再次提出精细化需求，换班功能需支持任意两个日期的任意两个专业对调。
        *   **技术决策:** 必须将`swap_duty_schedule`函数的签名升级为接收4个核心参数 `(date1, role1, date2, role2)`。核心技术是使用字典映射来提高代码可读性，并使用`getattr`/`setattr`动态属性技术来避免写出冗长复杂的`if/else`判断。
        *   **技术实现 (重构):** `src/services.py`中的`swap_duty_schedule`被重写为最终版本。
            ```python
            # 引入角色名到数据库字段名的映射，这是避免硬编码的关键
            ROLE_TO_FIELD_MAP = {
                '全专业值班': 'employee_full_professional',
                'CS专业投诉值班': 'employee_cs_complaint',
                # ...
            }
            def swap_duty_schedule(db, date1, role1, date2, role2):
                # ... (参数和日期校验)
                # 使用映射获取真实的字段名，而不是if/else
                field1 = ROLE_TO_FIELD_MAP[role1]
                field2 = ROLE_TO_FIELD_MAP[role2]

                # 使用getattr/setattr动态读写对象属性，这是实现灵活交换的核心
                name1 = getattr(schedule1, field1)
                name2 = getattr(schedule2, field2)
                setattr(schedule1, field1, name2)
                setattr(schedule2, field2, name1)

                db.commit() # 在单个事务中提交，保证原子性
            ```

---

## 第五阶段: 设计确认与最终测试

*   **用户指令:** 用户对最终实现思路提出疑问，特别是关于`discover/execute`模式。
*   **AI响应与动作 (RESEARCH -> EXECUTE模式):**
    1.  **思路阐述 (RESEARCH):** AI详细解释了当前采用的`@tool`装饰器模式，是如何通过**自动化**的方式，实现了与传统`discover/execute`模式相同的**工具发现**（通过解析函数签名和文档字符串）和**工具执行**（通过直接的函数调用）功能，并强调了其在可维护性上的巨大优势。
    2.  **单元测试 (EXECUTE):**
        *   **技术决策:** 使用Python内置的`unittest`框架和内存中的`SQLite`数据库进行测试，以实现快速、独立的验证。
        *   **技术实现:** 创建了`tests/test_services.py`，并编写了三个核心测试函数。
        *   **遇到问题:** 首次运行测试，终端返回了精确的错误信息：
            ```
            ImportError: cannot import name 'schemas' from 'src' (...)
            ```
        *   **解决问题:** 根据错误回溯，定位到`src/services.py`中一个早期开发遗留的、未使用的`import schemas`语句，并将其安全移除。
        *   **成功通过:** 修复后，再次运行测试，终端返回成功信息：
            ```
            ...
            ----------------------------------------------------------------------
            Ran 3 tests in 0.255s

            OK
            ```

---

## 第六阶段: 项目交付与文档编写

*   **AI响应与动作 (REVIEW -> DOCUMENTATION模式):**
    1.  **最终审查 (REVIEW):** 对整个项目进行了最终的符合性、质量和安全审查，并在`mcp_mysql_exec_task.md`中记录了结论。
    2.  **文档编写 (DOCUMENTATION):**
        *   根据用户要求，创建了详尽的`project_document/deployment_and_usage_guide.md`。
        *   根据用户最新指令，重写此份**极致详细版**对话与决策日志，包含了关键技术实现细节，作为最终的学习与归档材料。

---

## 第七阶段: 最终健壮性升级 (最终交付)

*   **用户指令:** 用户提出了一个至关重要的、关于长期可用性的问题：Excel的列名无法保证永远不变，当前的“硬编码”设计存在巨大风险。用户提议实现列名的自动读取。
*   **AI响应与动作 (INNOVATE -> EXECUTE -> DOCUMENTATION模式):**
    1.  **方案设计 (INNOVATE):** AI确认了用户提出的风险，并设计了“位置映射”方案，将依赖从脆弱的“列名”转移到更可靠的“列位置”上。核心假设变更为：无论列名如何，第一列永远是日期，第2-5列永远是按顺序的四个值班专业。
    2.  **代码重构 (EXECUTE):**
        *   对 `src/services.py` 中的 `import_schedule_from_excel` 函数进行了最终重构。
        *   **核心实现:**
            ```python
            # 不再有硬编码的列名
            column_names = df.columns.tolist()

            # 检查列的数量，而不是名称
            if len(column_names) < 5:
                return "错误：Excel文件必须至少包含5列..."

            # 按位置动态分配列名
            date_col = column_names[0]
            full_prof_col = column_names[1]
            # ... (以此类推)
            
            # 后续逻辑使用这些动态获取的变量来取值
            employee_full_professional=row.get(full_prof_col)
            ```
    3.  **文档同步 (DOCUMENTATION):**
        *   同步更新了 `mcp_mysql_exec_task.md` 中的风险评估和任务日志。
        *   同步更新了 `deployment_and_usage_guide.md`，向最终用户明确说明了新的、基于列位置的核心要求。
        *   同步更新此份最终版日志，记录下本次关键的健壮性升级。 