### POLPO (Proven Ollama Llm Python Orchestrator)
# 
# - sends prompts to Ollama
# - detects tool calls
# - chooses the right MCP server
# - calls the tool
# - re‑prompts Ollama
# - returns final answer

import yaml
import re
import json
import requests
import asyncio

from mcp_client import MCPClient


class Polpo:
    TOOL_PATTERN = r"#tool:([\w_]+)@([\w_]+)\n({[\s\S]+?})"

    def __init__(self, config_path="config.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.model = config["ollama"]["model"]

        # Initialize MCP server clients
        self.mcp_clients = {
            server["name"]: MCPClient(server["url"])
            for server in config["mcp_servers"]
        }

    def query_ollama(self, prompt):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": self.model, "prompt": prompt},
            timeout=120
        )
        return response.json()["response"]

    def parse_tool_call(self, text):
        match = re.search(self.TOOL_PATTERN, text)
        if not match:
            return None
        tool_name, server_name, args_json = match.groups()
        return tool_name, server_name, json.loads(args_json)

    async def run(self, user_prompt: str):
        # Step 1: Send prompt to Ollama
        llm_output = self.query_ollama(user_prompt)

        # Step 2: Detect tool call pattern
        tool_call = self.parse_tool_call(llm_output)

        if not tool_call:
            return llm_output

        tool, server, args = tool_call

        if server not in self.mcp_clients:
            return f"Error: MCP server '{server}' not configured."

        mcp = self.mcp_clients[server]

        # Step 3: Call the MCP tool
        result = await mcp.call_tool(tool, args)

        # Step 4: Feed results back into Ollama
        followup = f"""
The tool `{tool}` on server `{server}` returned:

{json.dumps(result, indent=2)}

Please continue your answer to the user.
"""
        final = self.query_ollama(followup)
        return final