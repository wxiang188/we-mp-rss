# 第一阶段：前端构建 (Frontend Builder)
FROM node:18-alpine as frontend-builder
WORKDIR /app
# 复制前端源码
COPY web_ui/ ./web_ui/
WORKDIR /app/web_ui
# 安装依赖并编译前端
RUN npm config set registry https://registry.npmmirror.com && \
    npm install && \
    npm run build

# 第二阶段：运行环境 (Backend & Final)
FROM ghcr.io/rachelos/base-full:latest as werss-base
WORKDIR /app

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 安装后端依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 从第一阶段复制编译好的前端产物到 static 目录
COPY --from=frontend-builder /app/web_ui/dist ./static

# 初始化配置与脚本权限
RUN cp ./config.example.yaml ./config.yaml && \
    chmod +x install.sh && \
    chmod +x start.sh && \
    echo "1.0.$(date +%Y%m%d.%H%M)" >> docker_version.txt

# Railway 端口配置
ENV PORT=${PORT:-8001}
EXPOSE $PORT

# 启动命令
CMD ["/bin/bash", "start.sh"]
