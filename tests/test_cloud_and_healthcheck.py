import os
import asyncio
import json
import pytest

from src.services.healthcheck import start_healthcheck_server


def test_healthcheck_server():
    async def _run():
        test_port = 18088
        server = await start_healthcheck_server(test_port)
        assert server is not None

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", test_port)
            writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()

            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()

            assert b"HTTP/1.1 200 OK" in response
            assert b'"status": "healthy"' in response
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(_run())


def test_env_loader_fallback(monkeypatch, tmp_path):
    env_file = tmp_path / ".test_env"
    env_file.write_text("TELEGRAM_API_ID=998877\nTELEGRAM_CHAT_ID=123456\n", encoding="utf-8")

    from src.config import _load_env_file
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    _load_env_file(str(env_file))

    assert os.getenv("TELEGRAM_API_ID") == "998877"
    assert os.getenv("TELEGRAM_CHAT_ID") == "123456"
