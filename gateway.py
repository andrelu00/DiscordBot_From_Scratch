import json
from types import SimpleNamespace
from typing import Sequence
import websockets
import asyncio
from dataclasses import dataclass

GATEWAY_URL = "wss://gateway.discord.gg/"

@dataclass
class GatewayMessage():
    op: int
    data: object
    sequence: int
    name: str

def decode_msg(msg):
    obj = json.loads(msg)
    data = None
    seq = None
    name = None
    if "d" in obj:
        data = SimpleNamespace(**obj["d"])
    if "s" in obj:
        seq = obj["s"]
    if "t" in obj:
        name = obj["t"]
    return GatewayMessage(obj["op"], data, seq, name)

class GatewayCon(object):

    def __init__(self, token):
        self._token = token
        self._q = asyncio.Queue()
        self._pulse = 1

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_connection())

    async def _run_connection(self):
         wsurl = f"{GATEWAY_URL}/?v=9&encoding=json"
         async with websockets.connect(wsurl) as ws:
             recv = asyncio.create_task(self._recv_loop(ws))
             send = asyncio.create_task(self._send_loop(ws))
             ping = asyncio.create_task(self._ping_loop(ws))
             await ping
             await send
             await recv

    async def _recv_loop(self, ws):
        async for msg in ws:
            decoded = decode_msg(msg)
            try:
                await self.handle_message(decoded)
            except Exception as e:
                print(f"Exception in receive: {e}")

    async def _send_loop(self, ws):
        while True:
            try:
                msg = await self._q.get()
                strmsg = json.dumps(msg)
                if "token" in msg["d"]:
                    msg["d"]["token"] = "***"
                    print(msg)
                await ws.send(strmsg)
            except Exception as e:
                print(f"Exception in send: {e}")

    async def _ping_loop(self, ws):
        while True:
            await asyncio.sleep(self._pulse)
            ping = {"op": 11}
            await self.send(ping)

    async def handle_message(self, msg):
        pass

    async def send(self, msg):
        print("pushing msg to send")
        await self._q.put(msg)

class GatewayPrinter(GatewayCon):
    async def handle_message(self, msg):
        print(msg)

if __name__ == "__main__":
    con = GatewayPrinter("foo")
    con.run()