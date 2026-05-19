# PocketMCP Authentication Guide

## How Authentication Works

Your MCP server uses **Bearer Token Authentication** via HTTP headers. Here's how it works:

### Authentication Flow

```
1. LLM/Client sends request with Authorization header
   ↓
2. FastMCP auth middleware intercepts the request
   ↓
3. Token is validated against your auth provider
   ↓
4. If valid → AccessToken is created and request proceeds
   If invalid → 401 Unauthorized response
   ↓
5. Tools can access caller identity via get_access_token()
```

## Important: Auth Requires HTTP Transport

**Bearer tokens only work with HTTP/HTTPS transport**, not stdio!

❌ **Won't work:**
```bash
python main.py  # stdio mode - no HTTP headers
```

✅ **Will work:**
```bash
fastmcp run server/auth_server.py --transport streamable-http --port 8765
# or
fastmcp run server/auth_server.py --transport http --port 8765
```

## Three Auth Levels

Your `auth_server.py` supports three authentication modes:

### 1. Development Mode (Any Token)
```python
auth_provider = DebugTokenVerifier()
```
- Accepts **any non-empty token**
- Use for: Local development, testing auth wiring
- Security: ⚠️ None - anyone can access

### 2. Shared Secret (Current Setup)
```python
SECRET_TOKEN = "pocket-secret-2026"
auth_provider = DebugTokenVerifier(
    validate=lambda t: t == SECRET_TOKEN,
    client_id="pocketmcp-client",
    scopes=["tools:read", "tools:write"],
)
```
- Accepts **only the exact token** `"pocket-secret-2026"`
- Use for: Internal tools, single-team APIs
- Security: ⚠️ Basic - shared secret must be kept private

### 3. JWT Production (Recommended for Production)
```python
from fastmcp.server.auth.providers.jwt import JWTVerifier
auth_provider = JWTVerifier(
    jwks_uri="https://YOUR_DOMAIN/.well-known/jwks.json",
    issuer="https://YOUR_DOMAIN/",
    audience="YOUR_API_AUDIENCE",
)
```
- Validates cryptographically signed JWTs from Auth0, Azure AD, GitHub, etc.
- Use for: Production, multi-user, external-facing servers
- Security: ✅ Strong - cryptographic validation

## How LLMs Connect to Your Auth Server

### Option 1: Claude Desktop (Limited Auth Support)

⚠️ **Claude Desktop's MCP integration does NOT support custom HTTP headers for bearer tokens.**

Claude Desktop only supports:
- stdio transport (no auth possible)
- Basic command execution

**Workaround:** You would need to:
1. Create a proxy server that handles auth
2. Have Claude connect to the proxy via stdio
3. Proxy forwards authenticated requests to your HTTP server

### Option 2: Custom LLM Integration (Full Control)

If you're building your own LLM application, you can pass the bearer token:

```python
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth

async with Client(
    "http://localhost:8765/mcp",
    auth=BearerAuth("pocket-secret-2026")
) as client:
    result = await client.call_tool("whoami", {})
    print(result.data)
```

### Option 3: API Gateway Pattern (Production)

For production LLM integrations:

```
LLM → API Gateway (handles auth) → Your MCP Server
```

The API Gateway:
- Authenticates the LLM request
- Adds the bearer token
- Forwards to your MCP server
- Returns results to the LLM

## Testing Your Auth Server

### Start the server:
```bash
python server/auth_server.py
# or
fastmcp run server/auth_server.py --transport streamable-http --port 8765
```

### Test with the client:
```bash
python client/auth_client.py
```

This will test:
1. ✅ No token → 401 error
2. ✅ Wrong token → 401 error  
3. ✅ Correct token → success
4. ✅ Identity info available in tools

## Using Auth in Your Tools

Any tool can access the authenticated caller's information:

```python
from fastmcp.server.dependencies import get_access_token

@mcp.tool
def my_secure_tool() -> dict:
    token = get_access_token()
    
    if token is None:
        return {"error": "Not authenticated"}
    
    # Access caller information
    caller_id = token.client_id
    permissions = token.scopes
    
    return {
        "caller": caller_id,
        "permissions": permissions,
        "message": "You are authenticated!"
    }
```

## Security Best Practices

1. **Never commit tokens to git**
   - Use environment variables: `os.getenv("MCP_SECRET_TOKEN")`
   - Add `.env` to `.gitignore`

2. **Use HTTPS in production**
   ```bash
   fastmcp run server/auth_server.py --transport https --port 443
   ```

3. **Rotate tokens regularly**
   - Change `SECRET_TOKEN` periodically
   - Use JWT with short expiry times

4. **Implement rate limiting**
   - Already included in your middleware stack!
   - `RateLimitingMiddleware(max_requests_per_second=20.0)`

5. **Log authentication attempts**
   - Monitor failed auth attempts
   - Alert on suspicious patterns

## Common Issues

### "Auth not working with Claude Desktop"
- Claude Desktop doesn't support bearer token auth over stdio
- Use HTTP mode with a custom client instead

### "401 Unauthorized even with correct token"
- Verify you're using HTTP transport, not stdio
- Check the token matches exactly (no extra spaces)
- Ensure Authorization header format: `Bearer pocket-secret-2026`

### "How do I pass the token from an LLM?"
- The LLM itself doesn't pass tokens
- Your application code (that calls the LLM) must handle auth
- Use the FastMCP Client with BearerAuth as shown above

## Next Steps

1. **For development:** Keep using the shared secret mode
2. **For production:** Switch to JWT with a proper IdP (Auth0, Azure AD, etc.)
3. **For LLM integration:** Build a custom client that handles auth before calling your MCP server
