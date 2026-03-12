
FROM  --platform=$BUILDPLATFORM ghcr.io/rachelos/base-full:latest as werss-base
#

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# ENV PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple

# 复制Python依赖文件
FROM werss-base
COPY requirements.txt .
# 安装系统依赖
WORKDIR /app
RUN echo "1.0.$(date +%Y%m%d.%H%M)">>docker_version.txt
# 复制后端代码
ADD ./config.example.yaml  ./config.yaml
ADD . .
RUN chmod +x install.sh
RUN chmod +x start.sh

# Railway 端口配置
ENV PORT=${PORT:-8001}
EXPOSE $PORT

# 启动命令
CMD ["python3", "main.py", "-job", "True", "-init", "True"]
