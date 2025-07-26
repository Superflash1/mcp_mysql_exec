#!/usr/bin/env python3
"""
值班表管理MCP服务器启动脚本

这个脚本用于启动MCP服务器，支持stdio传输。

使用方法：
python start_mcp_server.py
"""

import sys
import os

# 添加项目根目录到Python路径，确保可以正确导入src模块
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    # 直接导入并运行
    from src.mcp_server import main
    main() 
    
## npx @modelcontextprotocol/inspector python start_mcp_server.py