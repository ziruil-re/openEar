# 安装 pydub 说明

## 问题
音阶练习无法生成音频文件，因为缺少 `pydub` 库。

## 解决方法

### 方法1：使用虚拟环境（推荐）

如果使用 `run_prod.sh` 启动服务器：

```bash
cd /Users/liuzirui/Desktop/openEar/openEar
source venv/bin/activate  # 激活虚拟环境
pip install pydub
```

### 方法2：直接安装

```bash
pip install pydub
```

### 方法3：从 requirements.txt 安装

```bash
cd /Users/liuzirui/Desktop/openEar/openEar
pip install -r requirements.txt
```

## 注意事项

1. **ffmpeg 依赖**：`pydub` 需要 `ffmpeg` 来处理音频文件
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg` 或 `sudo yum install ffmpeg`
   - Windows: 下载 ffmpeg 并添加到 PATH

2. **验证安装**：
   ```bash
   python3 -c "from pydub import AudioSegment; print('pydub 安装成功')"
   ```

3. **重启服务器**：安装后需要重启服务器才能生效

## 如果仍然无法生成音频

1. 检查 ffmpeg 是否安装：
   ```bash
   ffmpeg -version
   ```

2. 查看服务器日志：
   - 访问 `/logs` 页面
   - 或查看 `logs/error.log` 文件

3. 检查目录权限：
   ```bash
   ls -la static/audio/scale/
   ```

