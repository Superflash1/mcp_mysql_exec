# 值班表管理MCP服务器

## 项目说明

本项目已成功将原有的FastAPI应用转换为符合Model Context Protocol (MCP)标准的服务器，支持远程HTTP调用。

## 文件结构

```
mcp_mysql_exec/
├── src/
│   ├── mcp_server.py          # MCP服务器主文件
│   ├── main.py                # 原FastAPI应用（保留）
│   ├── services.py            # 业务逻辑层
│   ├── models.py              # 数据模型
│   ├── schemas.py             # 数据结构定义
│   ├── database.py            # 数据库配置
│   └── config.py              # 配置文件
├── start_mcp_server.py        # MCP服务器启动脚本
├── test_mcp_client.py         # MCP客户端测试脚本
├── requirements.txt           # 依赖包列表（已更新）
└── project_document/
    └── mcp_usage_guide.md     # 详细使用指南
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动MCP服务器
```bash
python start_mcp_server.py
```

### 3. 测试服务器
```bash
python test_mcp_client.py
```

## MCP工具功能对照表

| 原FastAPI端点 | MCP工具名称 | 功能描述 |
|--------------|-------------|----------|
| `/import_schedule/upload` | `import_schedule_upload` | 通过Base64内容导入排班表 |
| `/import_schedule/path` | `import_schedule_path` | 通过文件路径导入排班表 |
| `/get_duty_employee/` | `get_duty_employee` | 查询指定日期值班人员 |
| `/swap_duty_schedule/` | `swap_duty_schedule` | 交换值班安排 |
| `/get_swap_logs/` | `get_swap_logs` | 查询换班日志 |
| 新增 | `get_server_info` | 获取服务器信息 |

## 技术特性

- ✅ **MCP协议兼容**: 完全符合MCP标准
- ✅ **远程HTTP调用**: 使用streamable-http传输
- ✅ **保持原功能**: 所有原有业务逻辑不变
- ✅ **结构化输出**: 支持MCP结构化数据返回
- ✅ **错误处理**: 完善的异常处理机制
- ✅ **生命周期管理**: 自动数据库初始化和清理
- ✅ **多客户端支持**: 支持并发连接

## 服务器配置

- **监听地址**: `0.0.0.0:8000`
- **MCP端点**: `/mcp`
- **传输协议**: Streamable HTTP
- **完整URL**: `http://localhost:8000/mcp`

## 客户端连接示例

### Python
```python
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("get_duty_employee", {"duty_date": "today"})
```

### JavaScript/TypeScript
```typescript
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamable-http.js";

const transport = new StreamableHTTPClientTransport(new URL("http://localhost:8000/mcp"));
await client.connect(transport);
```

## 与原FastAPI应用的区别

| 特性 | FastAPI版本 | MCP版本 |
|------|-------------|---------|
| 协议 | HTTP REST API | Model Context Protocol |
| 传输 | 标准HTTP | Streamable HTTP |
| 接口 | RESTful端点 | MCP工具 |
| 文档 | OpenAPI/Swagger | 工具描述和参数定义 |
| 客户端 | HTTP客户端 | MCP客户端 |
| 数据格式 | JSON | MCP结构化内容 |

## 优势

1. **标准化协议**: 使用业界标准的MCP协议
2. **更好的工具集成**: 易于集成到各种AI应用和客户端
3. **结构化交互**: 支持结构化的工具调用和响应
4. **更好的错误处理**: MCP协议级别的错误处理
5. **生态系统支持**: 可与其他MCP服务器和客户端互操作

## 部署建议

### 开发环境
```bash
python start_mcp_server.py
```

### 生产环境
建议使用进程管理器（如systemd、supervisor等）来管理MCP服务器进程。

### Docker部署
可以基于Python镜像创建Docker容器：
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "start_mcp_server.py"]
```

## 注意事项

1. **端口配置**: 默认使用8000端口，确保不与其他服务冲突
2. **数据库连接**: 保持原有的数据库配置
3. **文件权限**: 使用文件路径导入时注意权限设置
4. **并发处理**: MCP服务器支持多客户端并发访问
5. **日志监控**: 服务器运行时会输出详细日志

## 进一步开发

如需扩展功能，可以：
1. 添加新的`@mcp.tool()`装饰的函数
2. 实现MCP资源（`@mcp.resource()`）
3. 添加MCP提示模板（`@mcp.prompt()`）
4. 集成认证和授权机制

## 相关文档

- [详细使用指南](./project_document/mcp_usage_guide.md)
- [MCP官方文档](https://modelcontextprotocol.io)
- [原项目文档](./project_document/deployment_and_usage_guide.md)

---

**转换完成时间**: 2024年12月
**MCP版本**: 基于Python SDK实现
**协议版本**: Model Context Protocol 标准 