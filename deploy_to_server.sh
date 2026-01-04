#!/bin/bash
# 服务器部署脚本
# 使用方法：在服务器上运行此脚本

set -e  # 遇到错误立即退出

echo "🚀 openEar 服务器部署脚本"
echo "================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 用户运行此脚本"
    echo "   使用: sudo bash deploy_to_server.sh"
    exit 1
fi

# 配置变量（根据实际情况修改）
PROJECT_DIR="/var/www/openEar/openEar"
DOMAIN_NAME=""
SERVER_IP=""

# 获取服务器 IP
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(curl -s https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
fi

echo "📋 配置信息："
echo "   项目目录: $PROJECT_DIR"
echo "   服务器 IP: $SERVER_IP"
if [ -n "$DOMAIN_NAME" ]; then
    echo "   域名: $DOMAIN_NAME"
fi
echo ""

# 询问是否继续
read -p "是否继续部署？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "📦 步骤 1/7: 安装系统依赖..."
apt update
apt install -y python3 python3-pip python3-venv nginx git ffmpeg

echo ""
echo "📁 步骤 2/7: 创建项目目录..."
mkdir -p /var/www
if [ ! -d "$PROJECT_DIR" ]; then
    echo "⚠️  项目目录不存在，请先上传代码到 $PROJECT_DIR"
    echo "   可以使用 Git 克隆或 SCP 上传"
    exit 1
fi

cd $PROJECT_DIR

echo ""
echo "🐍 步骤 3/7: 配置 Python 环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_prod.txt

echo ""
echo "📂 步骤 4/7: 创建必要目录..."
mkdir -p logs
mkdir -p instance
chown -R www-data:www-data logs instance static
chmod -R 755 logs instance static

echo ""
echo "🗄️  步骤 5/7: 初始化数据库..."
if [ -f "app.py" ]; then
    python3 -c "from app import app, db; app.app_context().push(); db.create_all()" || echo "⚠️  数据库初始化可能已存在"
fi

echo ""
echo "⚙️  步骤 6/7: 配置 Nginx..."

# 如果提供了域名，使用域名，否则使用 IP
SERVER_NAME=${DOMAIN_NAME:-$SERVER_IP}

cat > /etc/nginx/sites-available/openear <<EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    # 静态文件
    location /static {
        alias $PROJECT_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 反向代理
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    client_max_body_size 50M;
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/openear /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # 删除默认配置

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "🔧 步骤 7/7: 配置系统服务..."

cat > /etc/systemd/system/openear.service <<EOF
[Unit]
Description=openEar Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload

# 启动服务
systemctl start openear
systemctl enable openear

echo ""
echo "🔥 配置防火墙..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 服务状态："
systemctl status openear --no-pager -l
echo ""
echo "🌐 访问地址："
echo "   http://$SERVER_NAME"
if [ -n "$DOMAIN_NAME" ]; then
    echo ""
    echo "📝 下一步："
    echo "   1. 在域名注册商处配置 DNS A 记录指向 $SERVER_IP"
    echo "   2. 等待 DNS 生效（通常 5-30 分钟）"
    echo "   3. 运行以下命令配置 HTTPS："
    echo "      sudo certbot --nginx -d $DOMAIN_NAME"
fi
echo ""
echo "📋 常用命令："
echo "   查看服务状态: sudo systemctl status openear"
echo "   查看日志: sudo journalctl -u openear -f"
echo "   重启服务: sudo systemctl restart openear"
echo "   查看 Nginx 日志: sudo tail -f /var/log/nginx/error.log"
echo ""

