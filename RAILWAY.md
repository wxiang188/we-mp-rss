# We-MP-RSS Railway 部署配置
# 在 Railway 项目的 Variables 中添加以下环境变量：

# 必需配置
PORT=8001

# 数据库 (Railway 提供 MySQL 可选)
# 使用 SQLite (默认)
DB=sqlite:///data/db3.db
# 或使用 Railway MySQL:
# DB=mysql+pymysql://<username>:<password>@<host>/we-rss?charset=utf8mb4

# 可选：Redis (Railway 提供)
# REDIS_URL=redis://:password@redis.example.com:6379/0

# 可选：AI 配置 (MiniMax)
# MINIMAX_API_KEY=sk-your-api-key

# 可选：通知配置
# DINGDING_WEBHOOK=
# WECHAT_WEBHOOK=
# FEISHU_WEBHOOK=
# BARK_WEBHOOK=

# 安全配置
SECRET_KEY=your-secret-key-change-this
