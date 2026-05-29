# miot-skill

> 基于小米官方 [miot_kit](https://github.com/XiaoMi/xiaomi-miloco) SDK 的米家智能家居控制工具 — 让 AI 直接操控你的米家设备。提供 MCP Server、CLI 命令、Agent Skill 及小智 WebSocket 桥接，纯 Python，ARM64 可用，零 GPU 依赖。

## 特性

- 🏠 **官方 SDK 直连** — 基于小米官方 miot_kit，复用 OAuth + AES 加密协议，稳定可靠
- 📱 **终端扫码登录** — 运行即显示二维码，手机米家一扫授权，token 自动刷新
- 🔧 **多种接入方式** — MCP Server、CLI 命令、Agent Skill，按需选用
- 🔍 **模糊匹配** — 设备/场景名称智能搜索，说「台灯」就能找到
- 🌐 **小智适配** — 通过 `mcp_pipe.py` WebSocket 桥接，断线自动重连
- 🤖 **Agent Skill** — 内置 MCP 和 CLI 两种 Skill，AI 开箱即用
- 🐍 **全异步** — aiohttp 驱动，无同步阻塞，ARM64 / x64 通吃

## 快速开始

### 1. 获取 miot_kit

```bash
git clone --depth 1 https://github.com/XiaoMi/xiaomi-miloco.git ~/src/xiaomi-miloco
```

### 2. 安装

```bash
git clone https://github.com/pkgplus/miot-skill.git
cd miot-skill
python3 -m venv venv && source venv/bin/activate
pip install -e ~/src/xiaomi-miloco/miot_kit
pip install -e .
```

### 3. 扫码登录

```bash
python -m miot_skill login
```

终端会显示二维码，用手机米家 App 扫码授权。授权后浏览器会跳转到 `127.0.0.1`（打不开是正常的），把地址栏的完整 URL 粘贴回终端即可。

登录成功后会自动提示选择家庭（支持多选或全部）。选择后只会操作对应家庭的设备和场景。随时可通过以下命令重新选择：

```bash
python -m miot_skill homes
```

### 4. 使用

```bash
# 测试连接
python -m miot_skill test

# 启动 MCP Server（stdio 模式）
python -m miot_skill
```

## MCP 工具

| 工具 | 说明 |
|------|------|
| `list_devices` | 设备列表，支持按房间筛选 |
| `get_device` | 设备详情 + SPEC 定义（siid/piid） |
| `device_on` | 打开设备 |
| `device_off` | 关闭设备 |
| `device_toggle` | 切换开关（先读后写） |
| `get_prop` | 读取属性（siid/piid） |
| `set_prop` | 设置属性（siid/piid/value） |
| `device_action` | 执行动作（siid/aiid） |
| `list_scenes` | 场景列表 |
| `execute_scene` | 执行场景（名称模糊匹配） |
| `get_service_status` | 服务连接状态 |

## CLI 命令

除了 MCP 模式，还提供独立 CLI 命令用于调试或 Agent Skill 调用：

```bash
python -m miot_skill homes                      # 选择/切换家庭
python -m miot_skill devices [--room 房间名]   # 设备列表
python -m miot_skill device <设备名>            # 设备详情
python -m miot_skill on <设备名>                # 打开
python -m miot_skill off <设备名>               # 关闭
python -m miot_skill toggle <设备名>            # 切换
python -m miot_skill get <设备名> <siid> <piid> # 读属性
python -m miot_skill set <设备名> <siid> <piid> <value>  # 写属性
python -m miot_skill action <设备名> <siid> <aiid> [--args ...]  # 执行动作
python -m miot_skill scenes                     # 场景列表
python -m miot_skill scene <场景名>             # 执行场景
python -m miot_skill status                     # 连接状态
```

所有命令输出 JSON 格式，设备名/场景名支持模糊匹配。

## Agent Skills

项目内置两种 Agent Skill，位于 `skills/` 目录：

| Skill | 路径 | 调用方式 | 适用场景 |
|-------|------|----------|----------|
| **miot-mcp** | `skills/miot-mcp/` | MCP 工具调用 | Claude Code、小智等 MCP 环境 |
| **miot-cli** | `skills/miot-cli/` | Bash 执行 CLI 命令 | 无 MCP 环境时的回退方案 |

**MCP 版本**（推荐）：Server 长驻，连接复用，响应快。适合已配置 MCP Server 的环境。

**CLI 版本**：每次通过 Bash 执行独立命令，无需 MCP Server 运行。适合调试或无法注册 MCP 的场景。

### 安装 Skill

将 `skills/miot-mcp/` 或 `skills/miot-cli/` 复制到你的 Claude Code 项目 `.claude/skills/` 目录即可。

## 注册到 Claude Code

在项目 `.claude/settings.json` 中添加 MCP Server：

```json
{
  "mcpServers": {
    "miot-skill": {
      "type": "stdio",
      "command": "/path/to/miot-skill/venv/bin/python",
      "args": ["-m", "miot_skill"]
    }
  }
}
```

## 注册到 Hermes Agent

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  miot:
    command: /path/to/miot-skill/venv/bin/python
    args: [-m, miot_skill]
    timeout: 30
```

```bash
hermes mcp test miot
```

## 小智平台

通过 `mcp_pipe.py` 将本地 MCP Server 桥接到小智 WebSocket：

```bash
# 设置小智 MCP 端点
export MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=XXXXX

# 启动桥接（自动读取 mcp_config.json 中已启用的 server）
python mcp_pipe.py

# 或指定单个 server
python mcp_pipe.py miot-skill
```

特性：
- WebSocket 断线自动重连（指数退避，最大 10 分钟）
- 支持 stdio / sse / http 三种传输类型
- 多 server 并行桥接
- 兼容 `MCP_ENDPOINT` 和 `XIAOZHI_MCP_URL` 环境变量

## 架构

```
   ┌─────────────────┐
   │  小智平台         │  WebSocket
   │  api.xiaozhi.me  │
   └────┬────────────┘
        │ ws://
   ┌────▼────────────┐
   │  mcp_pipe.py     │  WebSocket ↔ stdio 桥接
   │                  │  自动重连 + 多 server
   └────┬────────────┘
        │ stdio
   ┌────▼────────────┐
   │  miot_skill      │  11 MCP 工具 + CLI
   │  server.py       │  FastMCP
   └────┬────────────┘
        │
   ┌────▼────────────┐
   │  proxy.py        │  token 自动刷新
   │                  │  设备/场景控制
   └────┬────────────┘
        │
   ┌────▼────────────┐
   │  miot_kit        │  OAuth2 / AES+RSA
   │  (小米官方 SDK)   │  全异步 aiohttp
   └────┬────────────┘
        │ HTTPS
   ┌────▼────────────┐
   │  小米 IoT 云     │
   │  mico.api        │
   └─────────────────┘
```

## 项目结构

```
miot-skill/
├── src/miot_skill/
│   ├── server.py       # MCP Server（FastMCP stdio）
│   ├── cli.py          # CLI 命令入口
│   ├── proxy.py        # 设备控制代理层
│   ├── auth.py         # OAuth 认证
│   ├── config.py       # 配置常量
│   └── __main__.py     # 入口分发
├── skills/
│   ├── miot-mcp/       # MCP 版 Agent Skill
│   └── miot-cli/       # CLI 版 Agent Skill
├── mcp_pipe.py         # 小智 WebSocket 桥接
├── mcp_config.json     # MCP Server 配置
└── pyproject.toml
```

## License

MIT
