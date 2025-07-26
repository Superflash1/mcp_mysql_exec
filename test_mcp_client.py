#!/usr/bin/env python3
"""
MCP客户端测试脚本

用于测试值班表管理MCP服务器的功能。
运行前请确保MCP服务器已启动（运行 python start_mcp_server.py）

使用方法：
python test_mcp_client.py
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_mcp_server():
    """测试MCP服务器的各种功能"""
    print("正在连接到MCP服务器...")
    
    try:
        # 连接到MCP服务器
        async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                print("✅ 成功连接到MCP服务器")
                
                # 1. 列出可用工具
                print("\n=== 列出可用工具 ===")
                tools = await session.list_tools()
                print(f"发现 {len(tools.tools)} 个工具:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 2. 获取服务器信息
                print("\n=== 获取服务器信息 ===")
                server_info_result = await session.call_tool("get_server_info", {})
                if hasattr(server_info_result, 'structuredContent') and server_info_result.structuredContent:
                    server_info = server_info_result.structuredContent
                    print(f"服务器名称: {server_info.get('server_name')}")
                    print(f"版本: {server_info.get('version')}")
                    print(f"传输方式: {server_info.get('transport')}")
                
                # 3. 查询今天的值班人员
                print("\n=== 查询今天的值班人员 ===")
                duty_result = await session.call_tool("get_duty_employee", {"duty_date": "today"})
                print(f"查询结果: {duty_result.content[0].text if duty_result.content else '无内容'}")
                
                # 4. 查询换班日志
                print("\n=== 查询换班日志 ===")
                logs_result = await session.call_tool("get_swap_logs", {})
                print(f"日志查询结果: {logs_result.content[0].text if logs_result.content else '无内容'}")
                
                # 5. 测试文件路径导入（示例，可能因文件不存在而失败）
                print("\n=== 测试文件路径导入功能 ===")
                import os
                project_root = os.path.dirname(os.path.abspath(__file__))
                test_file_path = os.path.join(project_root, "排班表.xlsx")
                
                if os.path.exists(test_file_path):
                    import_result = await session.call_tool("import_schedule_path", {
                        "file_path": test_file_path
                    })
                    print(f"导入结果: {import_result.content[0].text if import_result.content else '无内容'}")
                else:
                    print(f"测试文件不存在: {test_file_path}")
                    print("跳过文件导入测试")
                
                print("\n✅ 所有测试完成")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("1. MCP服务器正在运行 (python start_mcp_server.py)")
        print("2. 服务器监听在 http://localhost:8000/mcp")
        print("3. 没有防火墙阻止连接")

def main():
    """主函数"""
    print("值班表管理MCP客户端测试工具")
    print("=" * 50)
    asyncio.run(test_mcp_server())

if __name__ == "__main__":
    main() 