# 值班表管理MCP服务器使用指南

## 概述

这是一个基于Model Context Protocol (MCP)的值班表管理服务器，将原有的FastAPI应用转换为MCP服务，支持远程HTTP调用。

## 功能特性

- **智能导入排班表**: 支持Excel文件导入（Base64内容或文件路径）
- **值班人员查询**: 查询指定日期的值班安排
- **换班管理**: 支持两个员工之间的值班交换
- **操作审计**: 记录所有换班操作的日志
- **远程调用**: 使用MCP协议支持远程HTTP调用

## 安装和启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动MCP服务器

方式一：使用启动脚本
```bash
python start_mcp_server.py
```

方式二：直接运行模块
```bash
python -m src.mcp_server
```

方式三：使用源文件启动
```bash
cd src && python mcp_server.py
```

### 3. 服务器信息

- **传输方式**: Streamable HTTP
- **监听地址**: http://0.0.0.0:8000/mcp
- **协议**: Model Context Protocol (MCP)

## MCP工具列表

### 1. import_schedule_upload
通过Base64编码的文件内容导入排班表

**参数**:
- `file_content_b64` (string): Base64编码的Excel文件内容

**返回**: 操作结果状态和消息

### 2. import_schedule_path
通过服务器本地文件路径导入排班表

**参数**:
- `file_path` (string): 服务器上Excel文件的绝对路径

**返回**: 操作结果状态和消息

### 3. get_duty_employee
查询指定日期的值班安排

**参数**:
- `duty_date` (string, 可选): 查询日期，格式为"YYYY-MM-DD"，默认"today"

**返回**: 值班安排详情，包含各专业的值班人员

### 4. swap_duty_schedule
交换两个员工的值班安排

**参数**:
- `employee1_date` (string): 第一个员工的值班日期
- `employee1_name` (string): 第一个员工的姓名
- `employee2_date` (string): 第二个员工的值班日期
- `employee2_name` (string): 第二个员工的姓名

**返回**: 换班操作详情和结果

### 5. get_swap_logs
查询换班操作审计日志

**参数**: 无

**返回**: 按时间倒序排列的换班日志列表

### 6. get_server_info
获取MCP服务器信息和使用帮助

**参数**: 无

**返回**: 服务器信息和所有可用工具的说明

## MCP客户端连接示例

### Python客户端示例

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    # 连接到MCP服务器
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 列出可用工具
            tools = await session.list_tools()
            print(f"可用工具: {[tool.name for tool in tools.tools]}")
            
            # 调用工具 - 查询今天的值班人员
            result = await session.call_tool("get_duty_employee", {"duty_date": "today"})
            print(f"查询结果: {result}")
            
            # 获取服务器信息
            server_info = await session.call_tool("get_server_info", {})
            print(f"服务器信息: {server_info}")

if __name__ == "__main__":
    asyncio.run(main())
```

### TypeScript/JavaScript客户端示例

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamable-http.js";

async function main() {
    const client = new Client(
        {
            name: "duty-schedule-client",
            version: "1.0.0",
        },
        {
            capabilities: {},
        }
    );

    const transport = new StreamableHTTPClientTransport(
        new URL("http://localhost:8000/mcp")
    );
    
    await client.connect(transport);
    
    // 列出工具
    const tools = await client.listTools();
    console.log("可用工具:", tools.tools.map(t => t.name));
    
    // 调用工具
    const result = await client.callTool("get_duty_employee", {
        duty_date: "today"
    });
    console.log("查询结果:", result);
    
    await client.close();
}

main().catch(console.error);
```

## 错误处理

所有工具都会返回包含以下字段的响应：
- `status`: "success" 或 "error"
- `message`: 操作结果描述
- `data`: 具体的数据内容（成功时）

错误情况下，会返回详细的错误信息以便调试。

## 注意事项

1. **数据库依赖**: 服务器启动时会自动创建必要的数据库表
2. **文件路径**: 使用`import_schedule_path`时，确保服务器有权限访问指定路径
3. **数据格式**: Excel文件应遵循预定义的排班表格式
4. **并发访问**: 支持多个客户端同时连接和调用
5. **日志记录**: 所有换班操作都会被记录在审计日志中

## 故障排除

### 常见问题

1. **连接失败**: 检查服务器是否正在运行，端口8000是否被占用
2. **工具调用失败**: 检查参数格式是否正确，数据库连接是否正常
3. **文件导入失败**: 检查Excel文件格式和权限

### 日志查看

服务器运行时会输出详细的日志信息，包括：
- 数据库初始化状态
- 工具调用记录
- 错误信息

## 技术架构

- **协议**: Model Context Protocol (MCP) 
- **传输**: Streamable HTTP
- **框架**: FastMCP (基于MCP Python SDK)
- **数据库**: SQLAlchemy ORM
- **文件处理**: pandas + openpyxl

## 更多信息

- [MCP官方文档](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [项目原始文档](./deployment_and_usage_guide.md) 