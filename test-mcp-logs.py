#  test-mcp-logs.py tests logs retrieval for both journal base and standard syslog-style log files. It:
#   - connects to the MCP WebSocket server, 
#   - sends a request to retrieve logs with the word "error" from last 60 minutes, 
#   - and prints the response.
#  run in virtual env with: ./venv/bin/python3 test-mcp-logs.py

import asyncio
import json
import websockets

async def send_request(websocket, request_id, query, minutes):
    req = {
        'jsonrpc': '2.0',
        'id': request_id,
        'method': 'tools.call',
        'params': {
            'name': 'get_logs',
            'arguments': {
                'query': query,
                'minutes': minutes
            }
        }
    }
    await websocket.send(json.dumps(req))
    response = await websocket.recv()
    print(f"Request {request_id}: query={query!r} minutes={minutes}")
    print(response)
    print()

async def main():
    uri = 'ws://localhost:6001'
    async with websockets.connect(uri) as websocket:
        # Test standard syslog-style lookup first
        await send_request(websocket, 1, 'error', 60)

        # Test journal fallback on Debian-style systems
        await send_request(websocket, 2, 'crash', 60)

        # Test journal base functionality with systemd-specific query
        await send_request(websocket, 3, 'systemd', 60)

asyncio.run(main())