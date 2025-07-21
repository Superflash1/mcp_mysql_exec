# MCP服务器部署与使用指南

**项目:** `mcp_mysql_exec` (值班表管理MCP)
**版本:** 1.0.0
**文档作者:** AI (Sun Wukong)

---

## 目录
1.  [本地运行与测试指南](#1-本地运行与测试指南)
2.  [生产环境部署指南](#2-生产环境部署指南)
3.  [在Cherry-Studio中集成与调用指南](#3-在cherry-studio中集成与调用指南)

---

## 1. 本地运行与测试指南

本章节指导您如何在自己的开发计算机上成功运行并测试此MCP服务器。

### **先决条件**
*   **Python**: 版本 3.8 或更高。
*   **pip**: Python包管理工具。
*   **MySQL数据库**: 一个正在运行的MySQL实例，用于存储值班数据。
*   **Git**: 版本控制工具 (可选，用于拉取代码)。

### **步骤一：获取代码**
将本项目代码放置在您的开发目录中。

### **步骤二：安装项目依赖**
在您的终端中，进入项目根目录 (即`mcp_mysql_exec/`)，然后运行以下命令安装所有必需的Python库：
```bash
pip install -r requirements.txt
```

### **步骤三：配置环境变量**
这是最关键的一步，用于连接您的数据库。
1.  在项目根目录下，找到 `.env.example` 文件。
2.  复制该文件并重命名为 `.env`。**`.env`文件包含敏感信息，切勿提交到代码仓库。**
3.  打开 `.env` 文件，修改以下配置以匹配您本地的MySQL设置：
    ```dotenv
    # 数据库连接配置
    DB_HOST=127.0.0.1       # 您的MySQL服务器地址
    DB_PORT=3306            # 您的MySQL服务器端口
    DB_USER=root            # 您的MySQL用户名
    DB_PASSWORD=your_actual_password  # 您的MySQL密码 (请务必修改)
    DB_NAME=duty_schedule_db  # 您为本项目创建的数据库名
    ```

### **步骤四：准备数据库和数据**
1.  **创建数据库**: 请在您的MySQL中手动创建一个数据库，数据库名称应与您在 `.env` 文件中 `DB_NAME` 的设置保持一致。例如，执行SQL命令：`CREATE DATABASE duty_schedule_db;`
2.  **准备Excel文件**: 
    *   在项目根目录下，放置您的值班表Excel文件。
    *   **健壮性设计**: 本服务器现在可以适配**任意列名**的Excel文件，您无需再担心列名变化导致服务中断。
    *   **核心要求**: 您唯一需要保证的是Excel文件的**列的位置顺序**：
        *   **第1列 (A列)**: 必须是日期列。
        *   **第2列 (B列)**: 必须是“全专业值班”人员列。
        *   **第3列 (C列)**: 必须是“CS专业投诉值班”人员列。
        *   **第4列 (D列)**: 必须是“CS专业故障值班”人员列。
        *   **第5列 (E列)**: 必须是“PS专业值班”人员列。

### **步骤五：启动MCP服务器**
此项目是一个MCP工具集，它本身不是一个独立运行的服务，而是需要被一个**MCP托管框架**来加载和执行。

当您通过支持的框架（如Cherry Studio）加载此项目的 `src` 目录时，`src/main.py` 文件中的 `@tool` 装饰器会自动向框架注册以下三个工具，使其可以被大模型调用。

---

## 2. 生产环境部署指南

将此MCP服务部署到生产环境，需要考虑持久化运行、安全和日志等问题。

### **推荐方案：使用进程管理器**
为了确保MCP服务在服务器上7x24小时不间断运行，建议使用进程管理器，如 `Supervisor` (Linux) 或 `NSSM` (Windows)。

**以 `Supervisor` 为例的配置 (Linux):**
1.  安装 `supervisor`: `sudo apt-get install supervisor`
2.  在 `/etc/supervisor/conf.d/` 目录下创建一个新的配置文件，例如 `mcp_duty_schedule.conf`:
    ```ini
    [program:mcp_duty_schedule]
    command=/path/to/your/project/venv/bin/python -m mcp_host_framework --load /path/to/your/project/src
    directory=/path/to/your/project/
    user=your_user
    autostart=true
    autorestart=true
    stderr_logfile=/var/log/mcp_duty.err.log
    stdout_logfile=/var/log/mcp_duty.out.log
    ```
    **注意**: `command` 中的 `mcp_host_framework` 是一个**假设的命令**，您需要替换为您实际使用的MCP托管框架的启动命令。

### **安全考量**
*   **环境变量**: 在生产环境中，强烈建议使用更安全的密钥管理服务（如HashiCorp Vault, AWS Secrets Manager等）来管理 `.env` 文件中的数据库密码，而不是将其明文存储在文件中。
*   **数据库**: 确保生产数据库的网络访问权限受到严格限制，只允许MCP服务器的IP地址进行访问。

---

## 3. 在Cherry-Studio中集成与调用指南

### **集成原理**
本MCP服务器采用了现代的**“装饰器”模式**进行工具注册。这意味着您不需要手动提供一个工具列表的JSON文件。当Cherry Studio加载本项目时，它会自动扫描代码，发现所有被 `@tool` 标记的函数，并将其解析为可用的工具。

### **通用集成步骤 (模板)**
请在您的Cherry Studio环境中，寻找类似 **“扩展工具”、“自定义MCP”或“工具集成”** 的设置选项。您很可能需要提供以下信息：

1.  **MCP名称**: `值班表管理` (或您喜欢的任何名称)
2.  **MCP代码路径**: `D:\code\mcp开发\mcp_mysql_exec` (指向本项目的根目录)
3.  **主入口模块/文件 (如果需要)**: `src/main.py`

完成上述配置后，Cherry Studio应该会自动完成“工具发现”过程。您可以在其工具列表或相关界面中看到我们开发完成的三个工具：
*   `import_schedule_from_excel`
*   `get_duty_employee`
*   `swap_duty_schedule`

### **工具调用示例**
集成成功后，您就可以在Cherry Studio的对话界面中，通过自然语言调用这些工具了。

**示例1：导入数据**
> **你**: "请帮我从 `D:\code\mcp开发\mcp_mysql_exec\排班表.xlsx` 文件导入最新的值班安排。"
>
> **Cherry Studio (调用MCP)**: `import_schedule_from_excel(file_path='D:\\code\\mcp开发\\mcp_mysql_exec\\排班表.xlsx')`

**示例2：查询值班**
> **你**: "今天谁值班？"
>
> **Cherry Studio (调用MCP)**: `get_duty_employee(duty_date='today')`

> **你**: "2024年10月1号谁值班？"
>
> **Cherry Studio (调用MCP)**: `get_duty_employee(duty_date='2024-10-01')`

**示例3：精准换班**
> **你**: "请将2024年10月1日的全专业值班人员与2024年10月8日的PS专业值班人员进行调换。"
>
> **Cherry Studio (调用MCP)**: `swap_duty_schedule(date1='2024-10-01', role1='全专业值班', date2='2024-10-08', role2='PS专业值班')` 