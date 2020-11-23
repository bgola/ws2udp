#!/usr/bin/env python

import asyncio
import websockets
import struct

async def example():
    proxy_uri = "ws://localhost:8765"
    addr = b"localhost"
    port = 57120
    async with websockets.connect(proxy_uri) as websocket:
        msg = b"hello, world"
        data = struct.pack('I', len(addr)) + addr + struct.pack('I', port) + msg
        await websocket.send(data)

asyncio.get_event_loop().run_until_complete(example())
