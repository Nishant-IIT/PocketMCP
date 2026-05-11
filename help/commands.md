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
# Standard dev mode
fastmcp dev main.py

# Or with explicit inspector flag
fastmcp dev inspector main.py
```
This runs the server with a browser UI to test tools interactively.

### Production Mode (stdio server)
```bash
fastmcp run main.py
```
Or simply:
```bash
python main.py
```

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
