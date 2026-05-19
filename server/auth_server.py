"""
Phase 7 — Authentication.

Auth in FastMCP works like this:
  - Pass an auth= provider to FastMCP(...).
  - The provider's verify_token(token) is called on every HTTP request.
  - If it returns None → 401 Unauthorized.
  - If it returns an AccessToken → the request proceeds.
  - The AccessToken is then available inside any tool via get_access_token().

Why HTTP is required:
  Bearer tokens travel in the Authorization header of HTTP requests.
  The in-memory and stdio transports have no such header — auth is
  meaningless there. Every real auth scenario needs HTTP transport.

Three auth configurations shown here (pick one at a time):
  1. DebugTokenVerifier()
      Accepts any non-empty token. The LLM can use any string.
      Use: local development where you just want the auth wiring to exist.

  2. DebugTokenVerifier(validate=lambda t: t == SECRET_TOKEN)
      Validates against a hardcoded string — the simplest "real" protection.
      Use: internal tools, shared secrets, single-team APIs.

  3. JWT providers (Auth0, Azure, GitHub, etc.)
      Validates a cryptographically signed JWT issued by an IdP.
      Use: production, multi-user, external-facing servers.
      → See fastmcp.server.auth.providers.jwt / auth0 / azure / github

AccessToken fields available inside tools:
  token      — the raw token string (truncate before logging!)
  client_id  — identifier for the calling application
  scopes     — list of permissions granted
  claims     — dict of additional claims from the token payload
  expires_at — expiry as a Unix timestamp (None = no expiry)
"""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.auth.providers.debug import DebugTokenVerifier
from fastmcp.server.dependencies import get_access_token

# ---------------------------------------------------------------------------
# Choose your auth level by uncommenting one of the three options below.
# ---------------------------------------------------------------------------

SECRET_TOKEN = "pocket-secret-2026"

# Option 1 — dev mode: any non-empty token is accepted
# auth_provider = DebugTokenVerifier()

# Option 2 — hardcoded token: only the exact string works (used in this demo)
auth_provider = DebugTokenVerifier(
    validate=lambda t: t == SECRET_TOKEN,
    client_id="pocketmcp-client",
    scopes=["tools:read", "tools:write"],
)

# Option 3 — JWT (production): uncomment and replace with your IdP config
# from fastmcp.server.auth.providers.jwt import JWTVerifier
# auth_provider = JWTVerifier(
#     jwks_uri="https://YOUR_DOMAIN/.well-known/jwks.json",
#     issuer="https://YOUR_DOMAIN/",
#     audience="YOUR_API_AUDIENCE",
# )

auth_mcp = FastMCP(
    name="PocketMCP-Auth",
    auth=auth_provider,
    instructions="Auth-protected server. All requests require a valid bearer token.",
)


@auth_mcp.tool
def whoami() -> dict:
    """
    Return information about the authenticated caller.
    Uses get_access_token() to read the AccessToken injected by the auth layer.
    This is the standard pattern for identity-aware tools.
    """
    token = get_access_token()
    if token is None:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "client_id":     token.client_id,
        "scopes":        token.scopes,
        "token_preview": token.token[:8] + "...",
        "claims":        token.claims,
    }


@auth_mcp.tool
def echo_secure(message: str) -> str:
    """
    Echo a message back. Only reachable if the bearer token is valid.
    The auth layer rejects the entire request before this function runs
    if the token is missing or invalid — no per-tool code needed.
    """
    token = get_access_token()
    caller = token.client_id if token else "unknown"
    return f"[{caller}] {message}"


if __name__ == "__main__":
    # Run as:  uv run python server/auth_server.py
    # Or:      uv run fastmcp run server/auth_server.py --transport streamable-http --port 8765
    auth_mcp.run(transport="streamable-http", port=8765)
