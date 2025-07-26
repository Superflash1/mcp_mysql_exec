#!/usr/bin/env python3
"""
直接测试MCP服务器功能的脚本
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_mcp_server():
    """测试MCP服务器的基本功能"""
    try:
        print("正在导入MCP服务器模块...")
        from src.mcp_server import mcp
        
        print("✅ MCP服务器模块导入成功")
        
        # 测试工具列表
        print("\n=== 测试工具发现 ===")
        
        # 获取所有注册的工具
        tools = list(mcp._tool_handlers.keys()) if hasattr(mcp, '_tool_handlers') else []
        print(f"发现 {len(tools)} 个工具:")
        for tool_name in tools:
            print(f"  - {tool_name}")
        
        # 测试服务器信息工具
        print("\n=== 测试服务器信息工具 ===")
        try:
            from mcp.server.fastmcp import Context
            
            # 创建一个模拟的Context对象
            class MockContext:
                pass
            
            mock_ctx = MockContext()
            
            # 直接调用get_server_info工具
            from src.mcp_server import get_server_info
            import asyncio
            
            async def test_server_info():
                info = await get_server_info(mock_ctx)
                return info
            
            server_info = asyncio.run(test_server_info())
            print(f"✅ 服务器信息获取成功:")
            print(f"   名称: {server_info.get('server_name')}")
            print(f"   版本: {server_info.get('version')}")
            print(f"   可用工具数量: {len(server_info.get('available_tools', []))}")
            
        except Exception as e:
            print(f"❌ 服务器信息工具测试失败: {e}")
        
        print("\n=== MCP服务器基本功能测试完成 ===")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("可能的原因:")
        print("1. MCP依赖包未安装: pip install mcp[cli]")
        print("2. 其他依赖包缺失")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        print("\n=== 测试数据库连接 ===")
        from src.database import engine, db_available
        
        if db_available:
            print("✅ 数据库连接正常")
        else:
            print("⚠️  数据库连接失败，使用SQLite内存数据库")
        
        # 测试数据库引擎
        print(f"数据库引擎: {engine.url}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("值班表管理MCP服务器直接测试")
    print("=" * 50)
    
    success = True
    
    # 测试数据库
    if not test_database_connection():
        success = False
    
    # 测试MCP服务器
    if not test_mcp_server():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 所有测试通过！MCP服务器应该可以正常工作")
        print("\n下一步可以:")
        print("1. 使用 python start_mcp_server.py 启动服务器")
        print("2. 使用 npx @modelcontextprotocol/inspector python start_mcp_server.py 调试")
    else:
        print("❌ 有些测试失败，请检查上述错误信息")
    
    return success

if __name__ == "__main__":
    main() 