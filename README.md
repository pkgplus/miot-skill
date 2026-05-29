# miot-mcp

小米米家智能家居 MCP Server — 基于小米官方 [miot_kit](https://github.com/XiaoMi/xiaomi-miloco) SDK 的纯 Python MCP 服务。

> 支持 ARM64（树莓派 5），零 GPU 依赖，全异步无阻塞。

## 特性

- 🏠 **小米云直连** — 基于 `miot_kit` 的 OAuth + AES 加密协议，稳定可靠
- 🔧 **11 个 MCP 工具** — 设备列表、开关控制、属性读写、场景执行
- 📱 **QR 扫码登录** — 一次扫码，token 持久化，自动刷新
- 🎯 **模糊匹配** — 设备/场景名称模糊搜索，说「打开台灯」就行
- 🌐 **小智平台适配** — 内置 `mcp_config.json` + WebSocket 桥接支持
- 🐍 **纯 Python** — aiohttp + cryptography，ARM64 / x64 通吃

## 安装

### 1. 获取 miot_kit

`miot_kit` 是小米 xiaomi-miloco 项目中的 MIoT 客户端库，需要先 clone：

```bash
# Clone xiaomi-miloco（只需 miot_kit 目录，其他 AI 引擎不需要）
git clone --depth 1 https://github.com/XiaoMi/xiaomi-miloco.git ~/src/xiaomi-miloco
```

> **说明**：`miot_kit` 是纯 Python 包（aiohttp + cryptography），不依赖 x86 架构或 NVIDIA GPU。
> xiaomi-miloco 仓库中的 `miloco_ai_engine/` 才需要 GPU，但 miot-mcp 不碰它。

### 2. 安装 miot-mcp

```bash
git clone https://github.com/pkgplus/miot-mcp.git
cd miot-mcp
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e ~/src/xiaomi-miloco/miot_kit   # miot_kit SDK
pip install -e .                                # miot-mcp 本体
```

### 3. 验证

```bash
python -m miot_mcp test --help
```

## 使用

### 1. 扫码登录

```bash
python -m miot_mcp login
```

复制链接 → 浏览器打开 → 手机米家扫码 → 复制回调 URL → 粘贴回终端。

### 2. 测试连接

```bash
python -m miot_mcp test
# ✅ 连接成功: 33 设备, 20 场景
```

### 3. 启动 MCP Server

```bash
python -m miot_mcp
```

## MCP 工具列表

| 工具 | 说明 |
|------|------|
| `list_devices` | 获取所有设备列表，支持按房间筛选 |
| `get_device` | 获取设备详细信息，含 SPEC 定义 |
| `device_on` | 打开设备（通用开关） |
| `device_off` | 关闭设备（通用开关） |
| `device_toggle` | 切换设备开关（先读后写） |
| `get_prop` | 读取设备属性（siid/piid） |
| `set_prop` | 设置设备属性（siid/piid/value） |
| `device_action` | 执行设备动作（siid/aiid） |
| `list_scenes` | 获取手动场景列表 |
| `execute_scene` | 执行场景（模糊匹配名称） |
| `get_service_status` | 查看 MCP 服务连接状态 |

## 注册到 Hermes Agent

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  miot:
    command: /path/to/miot-mcp/venv/bin/python
    args:
      - -m
      - miot_mcp
    timeout: 30
```

```bash
hermes mcp test miot
# ✓ Connected
# ✓ Tools discovered: 11
```

## 小智平台注册

1. 设置环境变量：

```bash
export XIAOZHI_REMOTE_URL=wss://your-xiaozhi-endpoint
export XIAOZHI_TOKEN=your-auth-token
```

2. 修改 `mcp_config.json`，启用远程 server：

```json
{
  "mcpServers": {
    "miot-mcp-remote": {
      "type": "sse",
      "url": "${XIAOZHI_REMOTE_URL}",
      "headers": {
        "Authorization": "Bearer ${XIAOZHI_TOKEN}"
      },
      "disabled": false
    }
  }
}
```

## 架构

```
┌─────────────────┐     MCP stdio     ┌──────────────────────┐
│  Hermes Agent   │ ◄──────────────► │    miot_mcp/server   │
│  / 小智 / Claude │                   │  (FastMCP, 11 tools) │
└─────────────────┘                   └──────────┬───────────┘
                                                 │
                                    ┌────────────▼───────────┐
                                    │     miot_mcp/proxy     │
                                    │  token 刷新 / 设备控制   │
                                    └────────────┬───────────┘
                                                 │
                                    ┌────────────▼───────────┐
                                    │       miot_kit         │
                                    │  (小米官方 SDK, 不改)    │
                                    │  AES+RSA / OAuth2       │
                                    └────────────┬───────────┘
                                                 │ HTTPS
                                    ┌────────────▼───────────┐
                                    │   mico.api.mijia.tech  │
                                    │    小米 MIoT Cloud      │
                                    └────────────────────────┘
```

## License

MIT
