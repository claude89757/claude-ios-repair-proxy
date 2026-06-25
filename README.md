# Claude iOS Repair Proxy

一个用于 Claude iOS App 登录卡死修复的临时代理服务，主要针对账号被 ban/禁用后，本地残留登录信息导致 App 启动时反复出现 `"Something went wrong, try again"` 且无法回到登录页的场景。

服务包含：

- HTTPS 指南网站和证书下载入口
- FastAPI 实时状态后端
- mitmproxy 修复代理
- 邀请码、专属代理端口和状态会话的服务端管理逻辑

## Issue Background

这个项目和 Claude iOS App 的 `"Something went wrong, try again"` 报错强相关。典型现象是账号被 ban、禁用或处于异常状态后，用户打开 App 只能看到错误提示，点击重试仍然回到同一个报错，删除并重装 App 也不一定能恢复登录入口。

相关讨论：

- [Reddit: "Something went wrong, try again" error. Help required.](https://www.reddit.com/r/ClaudeAI/comments/1tn3gf7/something_went_wrong_try_again_error_help_required/)

目前的判断是，这类问题主要来自被 ban/禁用账号的本地登录信息残留：Claude iOS App 继续携带旧的 session、cookie、routing hint 或设备认证状态启动，服务端返回账号或认证错误后，客户端仍持续重试旧登录态，而不是清理状态并展示登录页。本服务通过临时代理和受控 rewrite 流程，尝试让客户端收到正常的登录过期响应，从而清理残留状态并回到可重新登录的界面。

请只在自己的设备和账号上使用。不要提交、记录或共享真实 cookie、session key、mitmproxy 证书或其他敏感信息。

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
- `10001-10999`: per-invite Claude iOS repair proxy ports by default

## Security Notes

公开页面不内置代理账号密码。用户通过管理员发放的邀请码获取专属代理端口；iPhone Wi-Fi 代理认证保持关闭。修复代理只放行 Claude/Anthropic 相关域名和少量连通性测试域名，服务端只记录脱敏状态和事件元数据。
