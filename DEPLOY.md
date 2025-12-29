# Earcraft 部署指南

## 快速开始

### 方案1：开发环境（适合测试）

1. **启动服务器**
   ```bash
   ./run_dev.sh
   ```

2. **访问地址**
   - 本机：http://localhost:5001
   - 其他设备：http://你的IP地址:5001
   - 当前IP：运行 `ifconfig | grep "inet " | grep -v 127.0.0.1` 查看

3. **注意事项**
   - 确保其他设备与你的电脑在同一局域网（WiFi）内
   - 如果无法访问，检查防火墙设置

### 方案2：生产环境（推荐）

1. **安装依赖**
   ```bash
   source venv/bin/activate
   pip install -r requirements_prod.txt
   ```

2. **启动服务器**
   ```bash
   ./run_prod.sh
   ```

3. **访问地址**
   - 本机：http://localhost:5001
   - 其他设备：http://你的IP地址:5001

## 防火墙配置

### macOS
```bash
# 允许端口 5001
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/python
```

### Linux
```bash
# Ubuntu/Debian
sudo ufw allow 5001

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

## 云服务器部署

### 使用 Nginx 反向代理（推荐）

1. **安装 Nginx**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install nginx

   # CentOS/RHEL
   sudo yum install nginx
   ```

2. **配置 Nginx**
   创建 `/etc/nginx/sites-available/earcraft`：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # 或你的服务器IP

       location / {
           proxy_pass http://127.0.0.1:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **启用配置**
   ```bash
   sudo ln -s /etc/nginx/sites-available/earcraft /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **使用 systemd 管理 Gunicorn**
   创建 `/etc/systemd/system/earcraft.service`：
   ```ini
   [Unit]
   Description=Earcraft Gunicorn daemon
   After=network.target

   [Service]
   User=your-username
   Group=your-group
   WorkingDirectory=/path/to/openEar/openEar
   Environment="PATH=/path/to/openEar/openEar/venv/bin"
   ExecStart=/path/to/openEar/openEar/venv/bin/gunicorn -c gunicorn_config.py app:app

   [Install]
   WantedBy=multi-user.target
   ```

   启动服务：
   ```bash
   sudo systemctl start earcraft
   sudo systemctl enable earcraft
   ```

## 常见问题

### 1. 其他设备无法访问
- 检查防火墙是否允许端口 5001
- 确保设备在同一局域网
- 检查路由器是否开启了 AP 隔离

### 2. 端口被占用
修改 `app.py` 或 `gunicorn_config.py` 中的端口号

### 3. 性能优化
- 使用 Gunicorn 而不是 Flask 开发服务器
- 增加 workers 数量（根据 CPU 核心数）
- 使用 Nginx 作为反向代理

## 安全建议

1. **生产环境不要使用 debug=True**
2. **使用 HTTPS**（配置 SSL 证书）
3. **设置强密码**（如果启用用户认证）
4. **定期更新依赖包**

