"""
The Last 5% - 启动脚本
杠精选品助手 - 一键启动
"""

import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      ⚠️  THE LAST 5% - 杠精选品助手                          ║
    ║                                                              ║
    ║      专注于告诉你「为什么不该买」                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 启动服务器...")
    print("📍 访问地址: http://localhost:8000")
    print("📖 API 文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend", "frontend"]
    )
