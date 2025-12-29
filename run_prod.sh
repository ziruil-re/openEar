#!/bin/bash
# 生产环境启动脚本（使用 Gunicorn）

echo "🚀 启动 Earcraft 生产服务器..."
echo ""

# 创建日志目录
mkdir -p logs

# 激活虚拟环境
source venv/bin/activate

# 检查是否安装了 gunicorn
if ! command -v gunicorn &> /dev/null; then
    echo "📦 安装 Gunicorn..."
    pip install gunicorn
fi

# 获取本机 IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "📱 服务器地址："
echo "   本地访问：http://localhost:5001"
echo "   局域网访问：http://${LOCAL_IP}:5001"
echo ""
echo "💡 按 Ctrl+C 停止服务器"
echo ""

# 使用 Gunicorn 启动（捕获错误）
if gunicorn -c gunicorn_config.py app:app; then
    echo "✅ 服务器已启动"
else
    echo "❌ 服务器启动失败，请查看 logs/error.log 获取详细信息"
    exit 1
fi

