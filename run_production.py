#!/usr/bin/env python3
"""
生产环境启动脚本
使用 gunicorn 运行 Flask 应用
"""
import os
import sys

# 确保在正确的目录
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

if __name__ == '__main__':
    # 开发模式：直接运行（仅用于测试）
    from app import app
    # 生产环境应该使用 gunicorn，这里只是备用方案
    # 使用 0.0.0.0 让所有网络接口可访问
    app.run(host='0.0.0.0', port=5001, debug=False)

