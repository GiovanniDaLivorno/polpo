import asyncio
import websockets
import json
import uuid

### super simple MCP client
class McpClient:
    def __init__(self, url):
        self.url = url

    async def call_tool(self, tool, args):
        async with websockets.connect(self.url) as ws:
            message = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools.call",
                "params": {"name": tool, "arguments": args}
            }
            await ws.send(json.dumps(message))
            response = await ws.recv()
            return json.loads(response)["result"]