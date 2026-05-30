# -*- coding: utf-8 -*-
"""OAuth 回调捕获 — 临时 HTTPS :443 服务器。"""
import asyncio
import datetime
import ipaddress
import logging
import ssl
import tempfile

from aiohttp import web
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

_LOGGER = logging.getLogger(__name__)

SUCCESS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>登录成功</title></head>
<body style="display:flex;justify-content:center;align-items:center;height:100vh;font-family:system-ui;">
<div style="text-align:center;">
<h2>✅ 登录成功</h2>
<p>请返回 miot-x 页面继续操作。</p>
<script>
try { window.close(); } catch(e) {}
</script>
</div>
</body></html>"""


def _generate_self_signed_cert():
    """生成临时自签证书，返回 (cert_path, key_path)。"""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    cert_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
    key_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    cert_file.close()
    key_file.write(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ))
    key_file.close()
    return cert_file.name, key_file.name


async def start_callback_server() -> tuple[asyncio.Future | None, web.AppRunner | None]:
    """启动 HTTPS :443 临时服务器捕获 OAuth 回调 code。

    Returns:
        (code_future, runner) — code_future 会在收到 code 时 resolve。
        如果无法绑定 443 则返回 (None, None)。
    """
    code_future = asyncio.get_event_loop().create_future()

    async def handle_callback(request):
        code = request.query.get("code")
        if code and not code_future.done():
            code_future.set_result(code)
        return web.Response(text=SUCCESS_HTML, content_type="text/html")

    app = web.Application()
    app.router.add_get("/", handle_callback)

    cert_path, key_path = _generate_self_signed_cert()
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(cert_path, key_path)

    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "127.0.0.1", 443, ssl_context=ssl_ctx)
        await site.start()
        _LOGGER.info("OAuth 回调服务已启动 (https://127.0.0.1:443)")
        return code_future, runner
    except OSError as e:
        _LOGGER.warning("无法绑定 443 端口: %s（将使用手动模式）", e)
        await runner.cleanup()
        return None, None


async def stop_callback_server(runner: web.AppRunner | None):
    """停止回调服务器。"""
    if runner:
        await runner.cleanup()
        _LOGGER.info("OAuth 回调服务已停止")
