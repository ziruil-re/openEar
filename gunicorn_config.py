# Gunicorn 配置文件（生产环境）

# 服务器socket
bind = "0.0.0.0:5001"

# 工作进程数（建议：CPU核心数 * 2 + 1）
# macOS 上建议使用较少的工作进程
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1

# 工作进程类型
worker_class = "sync"

# 超时时间（秒）
timeout = 120

# 日志级别
loglevel = "info"

# 访问日志文件
accesslog = "logs/access.log"

# 错误日志文件
errorlog = "logs/error.log"

# 进程名称
proc_name = "earcraft"

# 守护进程模式（后台运行）
daemon = False

# 注意：worker_tmp_dir 在 macOS 上不需要设置，使用系统默认的临时目录

