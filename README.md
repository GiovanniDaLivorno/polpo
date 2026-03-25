
# POLPO

POLPO (Playful Ollama LLM Python Orchestrator) is a system that enables Large Language Models (LLMs) running on Ollama to interact with external tools via the Model Context Protocol (MCP). It acts as an orchestrator that detects tool calls in LLM responses, routes them to appropriate MCP servers, and feeds the results back to the LLM for a final answer.

## Features

- **LLM Integration**: Seamlessly integrates with Ollama-hosted LLMs.
- **Tool Calling**: Detects and executes tool calls specified in LLM responses.
- **MCP Support**: Communicates with MCP servers over WebSockets.
- **Modular Design**: Easy to add new MCP servers and tools.
- **Dockerized**: Fully containerized for easy deployment.

## Project Structure

```
polpo/
├── docker-compose.yml
├── example-app.py
├── README.md
├── system-prompt.txt
├── polpo/
│   ├── Dockerfile
│   ├── Polpo.py
│   ├── McpClient.py
│   └── config.yaml
├── mcp-logs/
│   ├── Dockerfile
│   └── server.py
└── mcp-metrics/
    ├── Dockerfile
    └── server.py
```

## Prerequisites

- Docker and Docker Compose
- Ollama installed and running (or use the provided Docker setup)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd polpo
   ```

2. Ensure Ollama is running. The docker-compose.yml includes an Ollama service using the `giod/molly` image.

3. Build and start the services:
   ```bash
   docker-compose up --build
   ```

## Usage

### Running the Example

The `example-app.py` demonstrates how to use POLPO:

```python
import asyncio
from polpo import Polpo

async def main():
    polpo = Polpo()
    response = await polpo.run("Check recent ERROR logs and tell me main issues.")
    print("\n=== FINAL ANSWER ===\n")
    print(response)

asyncio.run(main())
```

### System Prompt

When prompting the LLM, use the format specified in `system-prompt.txt`:

```
When you need external information, call a tool in this format:

#tool:TOOL_NAME@SERVER_NAME
{ "arg1": "", "arg2": "" }

Only use this format.
```

### Example Interaction

- User prompt: "Check errors in the logs from the last hour."
- LLM might respond:
  ```
  #tool:get_logs@logs_server
  {
    "query": "ERROR",
    "minutes": 60
  }
  ```
- POLPO detects the tool call, invokes the MCP server, gets data, and prompts the LLM for the final answer.

## Configuration

Edit `polpo/config.yaml` to configure MCP servers and the Ollama model:

```yaml
mcp_servers:
  - name: logs_server
    url: "ws://localhost:6001"
  - name: metrics_server
    url: "ws://localhost:6002"

ollama:
  model: "llama3"
```

## Adding New MCP Servers

1. Create a new directory with a `Dockerfile` and `server.py`.
2. Implement the MCP handler in `server.py`.
3. Add the service to `docker-compose.yml`.
4. Update `config.yaml` with the new server details.

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

[Specify your license here]