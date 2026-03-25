import asyncio
import json
import websockets

async def handler(websocket):
    async for msg in websocket:
        req = json.loads(msg)

        if req["method"] == "tools.call":
            name = req["params"]["name"]

            if name == "get_logs":
                query = req["params"]["arguments"]["query"]
                minutes = req["params"]["arguments"]["minutes"]

                result = {
                    "logs": [
                        f"Fake log entry with query '{query}' in last {minutes} minutes"
                    ]
                }

                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req["id"],
                    "result": result
                }))

async def main():
    async with websockets.serve(handler, "0.0.0.0", 6001):
        await asyncio.Future()

asyncio.run(main())