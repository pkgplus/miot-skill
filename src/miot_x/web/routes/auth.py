# -*- coding: utf-8 -*-
"""认证相关 API routes。"""
import json
import logging
import time

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ...lib.auth import MIoTAuth
from ...lib.config import AUTH_FILE
from ...lib.proxy import reset_shared_proxy
from ..oauth_callback import is_callback_available

_LOGGER = logging.getLogger(__name__)


async def auth_status(request: Request):
    """获取登录状态。"""
    if not AUTH_FILE.exists():
        return JSONResponse({"logged_in": False})
    try:
        data = json.loads(AUTH_FILE.read_text())
        expires_ts = data.get("expires_ts", 0)
        logged_in = bool(data.get("access_token")) and expires_ts > time.time()
        return JSONResponse({"logged_in": logged_in, "expires_ts": expires_ts})
    except Exception:
        return JSONResponse({"logged_in": False})


async def auth_start(request: Request):
    """启动 OAuth 登录流程，返回 OAuth URL。"""
    auth = MIoTAuth()
    auth_url, state = await auth.gen_oauth_url()

    return JSONResponse({
        "auth_url": auth_url,
        "auto_callback": is_callback_available(),
    })


async def auth_callback(request: Request):
    """手动提交 OAuth code（fallback 模式）。"""
    body = await request.json()
    code = body.get("code", "").strip()
    if not code:
        return JSONResponse({"success": False, "error": "missing code"}, status_code=400)

    try:
        auth = MIoTAuth()
        await auth.gen_oauth_url()
        await auth.exchange_code(code)
        await reset_shared_proxy()
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def auth_logout(request: Request):
    """登出（清除 token）。"""
    MIoTAuth.clear()
    return JSONResponse({"success": True})


routes = [
    Route("/auth/status", auth_status, methods=["GET"]),
    Route("/auth/start", auth_start, methods=["POST"]),
    Route("/auth/callback", auth_callback, methods=["POST"]),
    Route("/auth/logout", auth_logout, methods=["POST"]),
]
