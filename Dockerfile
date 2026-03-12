
FROM  --platform=$BUILDPLATFORM ghcr.io/rachelos/base-full:latest as werss-base
#

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# ENV PIP_INDEX_URL=https://mirrors.huaweicloud.com/repository/pypi/simple

# 复制Python依赖文件并安装
FROM werss-base
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN echo "1.0.$(date +%Y%m%d.%H%M)">>docker_version.txt
# 复制后端代码
ADD ./config.example.yaml  ./config.yaml
ADD . .
RUN chmod +x install.sh
RUN chmod +x start.sh

# Railway 端口配置
ENV PORT=${PORT:-8001}
EXPOSE $PORT

# 启动命令 (使用 start.sh 以便初始化环境)
CMD ["/bin/bash", "start.sh"]
