import asyncio
import logging
from typing import Optional

logger = logging.getLogger("healthcheck")


async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request_line = await reader.readline()
        # Read remaining headers
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n" or line == b"\n":
                break

        body = b'{"status": "healthy", "service": "telegram-monitor"}\n'
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n\r\n" + body
        )
        writer.write(response)
        await writer.drain()
    except Exception as e:
        logger.debug(f"Healthcheck error: {e}")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def start_healthcheck_server(port: int = 8080) -> Optional[asyncio.Server]:
    """
    Starts a minimal, zero-dependency HTTP server for cloud provider health probes.
    Listens on 0.0.0.0:port.
    """
    try:
        server = await asyncio.start_server(_handle_client, "0.0.0.0", port)
        logger.info(f"Healthcheck HTTP server listening on port {port}")
        return server
    except Exception as e:
        logger.warning(f"Could not bind healthcheck server on port {port}: {e}")
        return None

