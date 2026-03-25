import asyncio
import json
import websockets

async def handler(websocket):
    async for msg in websocket:
        req = json.loads(msg)

        if req["method"] == "tools.call":
            name = req["params"]["name"]

            if name == "get_cpu_metrics":
                interval = req["params"]["arguments"]["interval"]

                result = {
                    "cpu_percent": 27,
                    "interval": interval
                }

                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req["id"],
                    "result": result
                }))

async def main():
    async with websockets.serve(handler, "0.0.0.0", 6002):
        await asyncio.Future()

asyncio.run(main())
