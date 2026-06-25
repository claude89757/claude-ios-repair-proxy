# Claude iOS Repair Proxy

一个用于 Claude iOS App 登录卡死修复的临时代理服务。

服务包含：

- HTTPS 指南网站和证书下载入口
- FastAPI 实时状态后端
- mitmproxy 修复代理
- 邀请码、代理账号和状态会话的服务端管理逻辑

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

启动本地状态服务：

```bash
. .venv/bin/activate
uvicorn repair_site.status_app.main:app --host 127.0.0.1 --port 9000
```

## Configuration

复制 `.env.example` 为 `.env`，并填入生产环境自己的 secret。真实 `.env`、代理服务器凭据、mitmproxy 证书和 SQLite 数据库都不应提交。

## Ports

- `443`: Nginx public website
- `9000`: local FastAPI status backend
- `9443`: Claude iOS repair proxy

## Security Notes

公开页面不内置代理账号密码。用户通过管理员发放的邀请码获取临时代理配置；服务端只记录脱敏状态和事件元数据。
