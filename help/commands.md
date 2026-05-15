# PocketMCP - Basic Commands

## Setup

### Create Virtual Environment
```bash
# Using uv (recommended)
uv venv 
```

### Activate Virtual Environment
```bash
# On macOS/Linux
source .venv/bin/activate

# Or on Windows
.venv\Scripts\activate
```

### Install Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Add New Dependencies
```bash
# Add a package using uv
uv add fastmcp

# Add with specific version
uv add fastmcp>=3.2.4
```

## Running the Server

### Development Mode (with MCP Inspector)
```bash
# Run with MCP Inspector (browser UI to test tools)
fastmcp dev inspector main.py
```
This runs the server with a browser UI to test tools interactively.

### Production Mode

#### Option 1: stdio (default)
```bash
fastmcp run main.py
# or
python main.py
```
Best for: Claude Desktop integration, command-line clients

**How to interact:**
- Run the Python client: `python client/client.py`
- Add to Claude Desktop config (see below)
- Use with any MCP-compatible client

#### Option 2: HTTP Server
```bash
fastmcp run main.py --transport http
# or with custom host/port
fastmcp run main.py --transport http --host 0.0.0.0 --port 8080
```
Best for: Web applications, REST API access, remote connections

**How to interact:**
- Access at `http://localhost:8000/mcp/` (default)
- Use HTTP client or browser
- Connect from remote applications

#### Option 3: SSE (Server-Sent Events)
```bash
fastmcp run main.py --transport sse
```
Best for: Real-time streaming, web dashboards

**How to interact:**
- Access at `http://localhost:8000/sse/` (default)
- Receive real-time updates via SSE

### Claude Desktop Integration

Add to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "pocketmcp": {
      "command": "python",
      "args": ["/absolute/path/to/PocketMCP/main.py"]
    }
  }
}
```

### Development Mode with Auto-Reload
```bash
fastmcp run main.py --reload
# or with HTTP
fastmcp run main.py --transport http --reload
```
Automatically restarts the server when files change.

## Project Structure

```
PocketMCP/
├── server/          # Server implementation
│   ├── server.py    # Main MCP server setup
│   └── tools.py     # Tool definitions
├── client/          # Client implementation
├── main.py          # Entry point
└── pyproject.toml   # Project configuration
```

## Common Tasks

### Check Python Version
```bash
python --version
# Should be >= 3.14
```

### View Installed Packages
```bash
pip list
```

### Run Tests (if available)
```bash
pytest
```

## Dependencies

- **FastAPI** (>=0.136.1) - Web framework
- **FastMCP** (>=3.2.4) - MCP server framework

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
uv venv
uv sync
```

### Port Already in Use
If the development server fails to start, check if the port is already in use:
```bash
lsof -i :PORT_NUMBER
```

## Additional Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
