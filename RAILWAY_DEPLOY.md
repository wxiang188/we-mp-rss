# Railway 部署指南

本项目已适配 Railway 部署，Dockerfile 已包含 Railway 所需的端口配置。

## 部署步骤

### 1. 推送代码到 GitHub

将代码推送到你的 GitHub 仓库：

```bash
git add .
git commit -m "update for railway deployment"
git remote add origin https://github.com/你的用户名/we-mp-rss.git
git push -u origin main
```

### 2. 在 Railway 创建项目

1. 访问 [Railway](https://railway.app/) 并登录
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择 `we-mp-rss` 仓库

### 3. 配置环境变量

在 Railway 项目设置中添加以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | `8001` | 服务端口 |
| `DB` | `sqlite:///data/db.db` | 数据库连接 (SQLite) |
| `ENABLE_JOB` | `True` | 启用定时任务 |
| `WEB_NAME` | `WeRSS微信公众号订阅助手` | 网站名称 |

**注意**: Railway 免费版不支持持久化存储，SQLite 数据库会在容器重启后丢失数据。

### 4. 持久化存储配置 (推荐)

Railway 免费版需要配置持久化存储：

1. 在 Railway 仪表板，点击 "Volumes" -> "New Volume"
2. 创建一个 Volume 挂载到 `/app/data`

或者使用 MySQL/PostgreSQL 数据库：

```
DB=mysql+pymysql://user:password@host:3306/database?charset=utf8mb4
```

### 5. 部署完成

部署完成后，访问 Railway 提供的 URL 即可使用。

首次登录：
- 用户名: `admin`
- 密码: `admin@123`

## 常见问题

### Q: 部署后数据丢失
A: 免费版 Railway 容器重启后数据会丢失，建议使用付费版或使用外部数据库。

### Q: 微信公众号授权扫码不显示
A: 需要配置通知渠道才能收到授权二维码，或使用微信扫码枪。

### Q: 如何升级？
A: 每次代码推送到 GitHub 后，Railway 会自动重新部署。
