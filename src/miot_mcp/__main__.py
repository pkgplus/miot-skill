# -*- coding: utf-8 -*-
"""miot-mcp — 小米米家 MCP Server。

用法:
    python -m miot_mcp           # 启动 MCP stdio server
    python -m miot_mcp login     # 扫码登录
    python -m miot_mcp test      # 测试连接
"""
import asyncio
import re
import sys

from .server import main as server_main


async def login():
    """OAuth 扫码登录。"""
    from .auth import MIoTAuth

    auth = MIoTAuth()
    auth_url, state = await auth.gen_oauth_url()
    print(f"""
╔══════════════════════════════════════════════════════════╗
║               🔐 米家授权登录                            ║
╚══════════════════════════════════════════════════════════╝

📱 复制以下链接，在手机浏览器中打开并扫码:

{auth_url}

扫码授权后，浏览器会跳转到 127.0.0.1（无法打开是正常的），
把浏览器地址栏的 👉 完整 URL 👈 粘贴到这里:
""")

    callback_url = input("📋 回调 URL: ").strip()
    code_match = re.search(r'[?&]code=([^&]+)', callback_url)
    if not code_match:
        print("❌ URL 中未找到授权码 (code)")
        return

    code = code_match.group(1)
    try:
        oauth_info = await auth.exchange_code(code)
        print(f"""
✅ 登录成功!
   UID: {oauth_info.user_info.uid if oauth_info.user_info else 'N/A'}
   昵称: {oauth_info.user_info.nickname if oauth_info.user_info else 'N/A'}
   Token 已保存: ~/.miot-mcp/auth.json
""")
    except Exception as e:
        print(f"❌ 登录失败: {e}")


async def test():
    """测试设备连接。"""
    from .proxy import MiotProxy

    proxy = MiotProxy()
    await proxy.init()
    devices = await proxy.get_devices()
    scenes = await proxy.get_scenes()
    print(f"✅ 连接成功: {len(devices)} 设备, {len(scenes)} 场景")
    await proxy.deinit()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "login":
        asyncio.run(login())
    elif cmd == "test":
        asyncio.run(test())
    else:
        asyncio.run(server_main())


if __name__ == "__main__":
    main()
