# 使用轻量级 Python 3.9 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (如有需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY src/ ./src/

# 复制训练好的模型
COPY models/ ./models/

# 设置环境变量，确保 Python 能找到 src 模块
ENV PYTHONPATH=/app

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
