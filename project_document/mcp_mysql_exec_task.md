# 任务文件名: mcp_mysql_exec_task.md
**项目ID**: MCP_MYSQL_EXEC_2024
**创建时间**: 2024-05-20 10:00:00 +08:00
**最终更新**: 2024-05-21 18:00:00 +08:00
**创建者**: User & AI (Sun Wukong)
**关联协议**: RIPER-5 v4.1

---

## 任务描述

开发一个Python MCP（Model-Controller-Plugin）服务器，旨在实现对MySQL数据库中存储的值班表进行管理。服务器需具备以下核心功能：
1.  **数据初始化**:
    *   **拆分接口**: 提供两个独立的API，分别支持通过**上传Excel文件**和提供**服务器本地文件路径**进行数据导入。
    *   **智能路径处理**: 对于路径导入，服务器能自动处理Windows和Unix风格的路径，包括自动清理引号、空格，以及处理单、双反斜杠。
    *   **高性能**: 导入过程经过优化，能够快速处理文件，避免不必要的磁盘I/O和低效的数据迭代。
    *   **数据覆盖**: 导入新表时，旧数据（包括值班表和换班日志）将被清空。
2.  **智能查询**:
    *   能够根据指定日期（或“今天”）查询当日所有专业的值班人员。
    *   内置智能提醒：数据库为空时提示导入；查询日期为排班表最后一天时提醒更新。
3.  **按姓名精准换班**:
    *   **核心逻辑变更**: 允许用户通过API，指定两个日期和两个**员工姓名**，实现人员的精确对调。
    *   **歧义处理**: 服务器能够自动查找员工当天所在的岗位进行对调。如果找不到员工或一个员工在一天内担任多个角色（无法明确对调目标），将返回明确的错误提示。
4.  **可读的审计功能**:
    *   所有换班操作必须被记录到独立的日志表中。
    *   **格式化输出**: 提供API接口，用于查询所有换班审计日志。日志将以**人类可读的句子**形式返回（例如：“[时间] 换班申请: A日期的张三 与 B日期的李四 进行了对调。”），而不是原始的JSON数据。
5.  **API接口**:
    *   提供一个基于FastAPI的、带有交互式文档（Swagger UI）的Web API界面，方便测试和集成。
.
6.  **自动化与健壮性**:
    *   服务器启动时，能自动检测并创建所需的数据库（如果不存在）。
    *   能够灵活适应Excel列名变化，仅依赖列的固定位置进行数据解析。
    *   通过Pydantic模型对API的输入输出进行严格的数据校验。

---

## 1. 分析 (RESEARCH)

*   **核心发现**:
*   用户需求明确，涉及文件处理、数据库操作、API服务和业务逻辑，是一个典型的小型Web应用场景。
    *   项目的关键在于健壮性设计，需要处理好文件IO、数据库事务、API数据校验和环境差异。
*   **初步风险评估 (PM/AR) 及解决方案**:
    *   **数据源风险**: Excel表格的列名可能不固定。
        *   **[已解决]** **解决方案**: 采用“位置映射”策略。代码不依赖硬编码的列名，而是根据列的顺序（第1列日期，2-5列人员）来读
        取数据，增强了对不同Excel模板的适应性。
    *   **文件编码风险**: 用户（尤其在Windows环境）提供的`.env`配置文件或Excel文件可能存在非UTF-8编码（如GBK），导致读取错误。
        *   **[已解决]** **解决方案**: 在代码中明确处理了编码问题。加载`.env`时指定`encoding="gbk"`作为兼容方案；读取Excel时也
        增加了相应的编码处理逻辑。
    *   **数据结构风险**: 若API返回值为简单的字符串或无结构的JSON，将导致前端/调用方难以解析和使用，且容易在逻辑变更时出错。
        *   **[已解决]** **解决方案**: 引入Pydantic模型。为所有API的请求体和响应体定义了严格的数据结构（Schema），实现了自动的
        数据校验、序列化和文档生成，极大提升了接口的可靠性和可维护性。
    *   **数据库风险**:
        *   **连接信息硬编码**: 将数据库地址、密码等敏感信息写入代码，存在安全隐患。**[已解决]** 通过`.env`文件将配置与代码分
        离。
        *   **手动初始化**: 要求用户手动创建数据库和表，增加了部署的复杂性。**[已解决]** 实现自动化：① 使用
        `mysql-connector-python`在服务启动时检查并自动创建数据库。② 使用`SQLAlchemy`的`metadata.create_all()`自动创建所有表。
        *   **SQL注入**: 手动拼接SQL语句可能导致SQL注入攻击。**[已解决]** 全程使用SQLAlchemy ORM进行数据库操作，从根本上杜绝了
        SQL注入的风险。
*   **DW确认**: 分析记录完整、准确，风险及解决方案清晰，符合文档规范。
    *   除了基础的CRUD，用户对**性能、健壮性和用户体验**有非常高的要求，这使得项目从一个简单的功能实现，演变为一个需要综合考虑各种边界情况的、生产级的应用。
*   **最终风险评估 (PM/AR) 及解决方案**:
    *   **文件导入接口风险**: 单一接口同时处理文件上传和文件路径，在FastAPI中容易因表单数据处理机制导致`422`校验错误。
        *   **[已解决]** **解决方案**: 拆分为两个独立的API：`/import_schedule/upload` 和 `/import_schedule/path`，彻底规避了该问题。
    *   **文件路径风险**: 用户提供的文件路径格式多样（Windows的`\`，Unix的`/`，带引号，带空格等），直接使用容易出错。
        *   **[已解决]** **解决方案**: 实现了强大的路径自适应函数，在接收到路径后进行标准化处理（去空格、去引号、统一路径分隔符、规范化），使接口对用户输入更加宽容。
    *   **换班逻辑风险**: 按“专业”换班不直观。变更为按“姓名”换班后，可能出现员工当天有多个班次，导致换班目标不明确。
        *   **[已解决]** **解决方案**: 在核心换班逻辑中增加了前置检查。在执行换班前，会先查找员工当天的排班情况。如果找不到，或找到多于一个班次，则操作被终止，并向用户返回清晰的错误原因。
    *   **性能风险**: 对于较大的Excel文件，逐行读写数据库的性能可能很差。
        *   **[已解决]** **解决方案**: 重构了Excel处理逻辑。① 文件上传后在**内存中**直接处理，避免了磁盘的临时读写。② 使用`Pandas`的**向量化操作**和`to_dict('records')`代替低效的逐行遍历，大幅提升了数据处理速度。
    *   **审计日志可读性风险**: 直接返回数据库的原始JSON日志，不便于人类审计员快速理解。
        *   **[已解决]** **解决方案**: 在查询日志的服务层中，增加了格式化处理逻辑，将结构化的日志数据转换为统一、清晰的自然语言描述。

---

## 2. 方案设计 (INNOVATE)

*   **最终选定方案**: 构建一个基于FastAPI框架的、分层清晰的Web服务。
    *   **接口层 (main.py)**: 使用FastAPI构建Web API接口，负责接收请求、校验数据（通过Pydantic模型）、调用业务逻辑并返回结构化
    响应。利用FastAPI的特性自动生成交互式API文档。
    *   **业务逻辑层 (services.py)**: 封装所有核心业务逻辑，如解析Excel、操作数据库、处理换班逻辑、记录日志等。该层不直接与Web框
    架耦合，保证了逻辑的可重用性和可测试性。
    *   **数据模型层 (models.py)**: 使用SQLAlchemy ORM定义数据库表结构，将数据库表映射为Python对象。
    *   **数据结构层 (schemas.py)**: 使用Pydantic定义API的数据接口模型，用于请求和响应的数据验证。
    *   **配置层 (config.py)**: 使用`python-dotenv`加载`.env`文件，管理所有环境变量和配置信息。
    *   **数据库访问层 (database.py)**: 配置SQLAlchemy的数据库引擎和会话（Session），并实现数据库自动创建的逻辑。
*   **架构文档**: 本文档的方案设计部分即为核心架构描述。
*   **DW确认**: 方案设计清晰，分层合理，技术选型得当，符合文档规范。
*   **最终选定方案**: 与初始方案一致，但对细节进行了大量优化和增强，最终形成一个基于FastAPI框架的、分层清晰、逻辑健壮的Web服务。各层职责明确，保证了项目的可维护性和扩展性。

---

## 3. 实施计划 (PLAN)

*   **最终API接口定义:**
    1.  `GET /`: 提供一个欢迎页面，用于服务可用性检查。
    2.  `POST /import_schedule/upload`: **上传文件导入接口**。接收`multipart/form-data`格式的Excel文件。
    3.  `POST /import_schedule/path`: **文件路径导入接口**。接收一个包含`file_path`字段的JSON对象。
    4.  `GET /get_duty_employee/`: 查询指定日期的值班安排。接收`duty_date`作为查询参数。
    5.  `POST /swap_duty_schedule/`: **按姓名精准对调接口**。接收一个包含两个对调单元（每个单元含日期和员工姓名）的JSON对象作为请求体。
    6.  `GET /get_swap_logs/`: **查询换班审计日志**。返回一个包含人类可读日志字符串的列表。
*   **实施清单**:
    *   `[P3-AR-001]` **环境搭建**: 创建`requirements.txt`和`.env.example`文件。 **(已完成)**
    *   `[P3-AR-002]` **项目结构初始化**: 创建`src`目录及各模块文件 (`main.py`, `services.py`, etc.)。 **(已完成)**
    *   `[P3-LD-003]` **配置与数据库连接**: 实现`config.py`和`database.py`，包括数据库自动创建逻辑。 **(已完成)**
    *   `[P3-LD-004]` **模型定义**: 在`models.py`和`schemas.py`中定义所有数据库ORM模型和API数据模型。 **(已完成)**
    *   `[P3-LD-005]` **核心业务逻辑实现**: 在`services.py`中实现所有核心功能函数。 **(已完成)**
    *   `[P3-LD-006]` **API端点实现**: 在`main.py`中创建FastAPI应用，并实现所有API端点。 **(已完成)**
    *   `[P3-LD-007]` **调试与修复**: 解决开发过程中遇到的所有环境问题、编码问题和逻辑错误。 **(已完成)**
    8.  `[P3-DW-008]` **文档编写与最终迭代**: 完成所有项目文档的编写，并根据最终的功能变更进行全面更新。 **(已完成)**
*   **DW确认**: 实施计划与最终产出完全一致。

---

## 4. 当前执行步骤 (EXECUTE - Dynamic Update)
> `[MODE: COMPLETED]` 项目已于 2024-05-21 完成最终交付。

---

## 5. 任务进展 (EXECUTE - Append-only Log)
---
*   **时间**: 2024-05-21 17:30:00 +08:00
*   **执行项**: 响应用户反馈，进行最终的功能和体验优化。
*   **核心产出**:
    *   **接口拆分**: 将`/import_schedule/`拆分为`/upload`和`/path`两个更可靠的接口。
    *   **性能优化**: 重构了`services.py`中的导入逻辑，采用内存IO和向量化操作。
    *   **路径处理**: 增加了路径清理和规范化函数，增强了路径导入的健壮性。
    *   **换班逻辑重构**: 将换班功能从“按专业”修改为“按姓名”，并增加了歧义处理逻辑。
    *   **日志格式化**: 将日志查询结果从JSON对象修改为人类可读的字符串。
*   **状态**: 已完成
---

## 6. 最终审查 (REVIEW)
*   **总体结论**: 项目已达到并超越了最初设定的所有目标，是一个功能完整、设计良好、性能高效、文档齐全、健壮可靠的MCP服务。
*   **DW确认**: 审查报告内容完整，所有文档均已根据最终代码状态完成更新。项目正式关闭。 