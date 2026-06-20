FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY cache/ ./cache/
COPY data/ ./data/
COPY run.py .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run.py", "--prod"]
