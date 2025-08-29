#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本：Markdown to EPUB Web 服务
"""

import os
import sys
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Markdown to EPUB 转换器")
    print("=" * 60)
    print("📚 访问地址: http://localhost:5000")
    print("📚 外网访问: http://0.0.0.0:5000")
    print("⚡ 按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 生产环境配置
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    try:
        app.run(
            host=host,
            port=port, 
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)