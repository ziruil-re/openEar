#!/bin/bash
# 生产环境启动脚本（使用 Gunicorn）

echo "🚀 启动 Earcraft 生产服务器..."
echo ""

# 进入脚本所在目录
cd "$(dirname "$0")"

# 创建日志目录
mkdir -p logs

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    if [ -f "setup_venv.sh" ]; then
        ./setup_venv.sh
    else
        echo "❌ 错误：未找到 setup_venv.sh，请先运行：./setup_venv.sh"
        exit 1
    fi
fi

# 激活虚拟环境
source venv/bin/activate

# 检查是否安装了 gunicorn
if ! command -v gunicorn &> /dev/null; then
    echo "📦 安装 Gunicorn..."
    pip install gunicorn
fi

# 获取本机 IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

# 尝试获取公网 IP（如果可用）
PUBLIC_IP=$(curl -s https://api.ipify.org 2>/dev/null || echo "无法获取")

echo "📱 服务器地址："
echo "   本地访问：http://localhost:5001"
echo "   局域网访问：http://${LOCAL_IP}:5001"
if [ "$PUBLIC_IP" != "无法获取" ]; then
    echo "   公网访问：http://${PUBLIC_IP}:5001（需要配置端口转发）"
fi
echo ""

# 检查防火墙状态（macOS）
if command -v /usr/libexec/ApplicationFirewall/socketfilterfw &> /dev/null; then
    echo "🔒 防火墙检查："
    FW_STATUS=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -i "enabled" || echo "")
    if [ -n "$FW_STATUS" ]; then
        echo "   ⚠️  系统防火墙已启用，请确保允许 Python 或 Gunicorn 的连接"
        echo "   💡 如需允许外网访问，请在系统设置 > 网络 > 防火墙中配置"
    fi
    echo ""
fi

# 检查端口是否被占用
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告：端口 5001 已被占用"
    echo "   正在使用该端口的进程："
    lsof -Pi :5001 -sTCP:LISTEN
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    echo ""
fi

echo "💡 外网访问配置提示："
echo "   1. 确保路由器已配置端口转发（外部端口 5001 -> 本机IP:5001）"
echo "   2. 确保防火墙允许 5001 端口的入站连接"
echo "   3. 如果使用云服务器，确保安全组规则允许 5001 端口"
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

