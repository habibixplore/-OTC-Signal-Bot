import asyncio
import json
import websockets
from typing import Callable

import config


class DerivClient:
    def __init__(self, on_tick: Callable):
        self.on_tick = on_tick  # async callback(symbol, price)
        self.ws = None
        self.running = False

    async def connect(self):
        self.running = True
        while self.running:
            try:
                print(f"[DERIV] Connecting to {config.DERIV_WS_URL}")
                async with websockets.connect(config.DERIV_WS_URL) as ws:
                    self.ws = ws
                    print("[DERIV] Connected ✓")
                    await self._subscribe_all()
                    await self._listen()
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[DERIV] Connection closed: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[DERIV] Error: {e}. Reconnecting in 10s...")
                await asyncio.sleep(10)

    async def _subscribe_all(self):
        for symbol in config.OTC_SYMBOLS:
            payload = {
                "ticks": symbol,
                "subscribe": 1
            }
            await self.ws.send(json.dumps(payload))
            print(f"[DERIV] Subscribed to {symbol}")
            await asyncio.sleep(0.1)  # slight delay to avoid rate limiting

    async def _listen(self):
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                await self._handle_message(msg)
            except json.JSONDecodeError:
                continue

    async def _handle_message(self, msg: dict):
        msg_type = msg.get("msg_type")

        if msg_type == "tick":
            tick = msg.get("tick", {})
            symbol = tick.get("symbol")
            price = tick.get("quote")
            if symbol and price is not None:
                await self.on_tick(symbol, float(price))

        elif msg_type == "error":
            error = msg.get("error", {})
            print(f"[DERIV] API Error: {error.get('message')} (code: {error.get('code')})")

    def stop(self):
        self.running = False
