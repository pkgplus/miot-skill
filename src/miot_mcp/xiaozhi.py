# -*- coding: utf-8 -*-
"""小智 MCP 适配 — 解析 mcp_config.json，管理远程注册。"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class XiaozhiConfig:
    """小智 MCP 注册配置。"""

    def __init__(self, config_path: Path = None):
        self._config_path = config_path or Path(
            os.getenv("XIAOZHI_CONFIG", "mcp_config.json")
        )
        self._data: dict = {}

    # ── 配置加载 ───────────────────────────────────

    def load(self) -> dict:
        """加载 mcp_config.json。"""
        path = self._config_path
        if not path.exists():
            _LOGGER.warning("配置文件不存在: %s", path)
            return {}
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    @property
    def servers(self) -> dict:
        """获取所有注册的 MCP server。"""
        if not self._data:
            self.load()
        return self._data.get("mcpServers", {})

    @property
    def enabled_servers(self) -> dict:
        """获取所有启用的 server。"""
        return {
            name: cfg
            for name, cfg in self.servers.items()
            if not (cfg or {}).get("disabled", False)
        }

    # ── 远程配置 ───────────────────────────────────

    @staticmethod
    def get_remote_url() -> Optional[str]:
        """获取小智远程 WebSocket 端点。"""
        return os.getenv("XIAOZHI_REMOTE_URL")

    @staticmethod
    def get_token() -> Optional[str]:
        """获取小智认证 token。"""
        return os.getenv("XIAOZHI_TOKEN")

    # ── 注册信息生成 ───────────────────────────────

    def build_server_command(self, name: str) -> tuple[list[str], dict]:
        """根据配置生成 server 启动命令。

        Returns:
            (command_list, env_dict): subprocess 可用的命令和环境变量。
        """
        servers = self.servers
        if name not in servers:
            raise RuntimeError(f"未知 server: {name}")

        entry = servers[name]
        if entry.get("disabled"):
            raise RuntimeError(f"Server '{name}' 已禁用")

        typ = (entry.get("type") or "stdio").lower()
        env = os.environ.copy()
        for k, v in (entry.get("env") or {}).items():
            env[str(k)] = str(v)

        if typ == "stdio":
            cmd = entry.get("command")
            args = entry.get("args") or []
            if not cmd:
                raise RuntimeError(f"Server '{name}' 缺少 'command'")
            return [cmd, *args], env

        if typ in ("sse", "http", "streamablehttp"):
            url = entry.get("url")
            if not url:
                raise RuntimeError(f"Server '{name}' 缺少 'url'")

            # 替换环境变量占位符
            for var in ["XIAOZHI_REMOTE_URL", "XIAOZHI_TOKEN"]:
                placeholder = f"${{{var}}}"
                if placeholder in url:
                    url = url.replace(placeholder, os.getenv(var, ""))

            cmd = [os.sys.executable, "-m", "miot_mcp.server"]
            return cmd, env

        raise RuntimeError(f"不支持的 server 类型: {typ}")

    def to_json(self) -> str:
        """导出配置为 JSON 字符串。"""
        return json.dumps(self._data, indent=2, ensure_ascii=False)
