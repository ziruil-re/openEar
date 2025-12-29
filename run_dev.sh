#!/bin/bash
# 开发环境启动脚本（允许局域网访问）

echo "🚀 启动 Earcraft 开发服务器..."
echo ""
echo "📱 其他设备访问地址："
echo "   http://$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1):5001"
echo ""
echo "💡 确保其他设备与你的电脑在同一局域网内"
echo ""

# 激活虚拟环境并启动
source venv/bin/activate
python app.py

