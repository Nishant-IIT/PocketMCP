# PocketMCP — Learning Roadmap

A single growing codebase to learn MCP end-to-end using FastMCP.
Each phase builds on the last. Don't skip ahead.

---

## Phase 1 — Basic Server & Tools

**Goal:** Get a server running and understand how tools work at the protocol level.

### What you'll build
A FastMCP server with 3–4 utility tools (text, math, datetime).

### Steps
1. Set up project structure (`server/`, `client/` folders)
2. Create `server/server.py` with a bare `FastMCP` instance
3. Add tools in `server/tools.py` using `@mcp.tool`
4. Learn how type hints become the JSON schema Claude sees
5. Learn how docstrings become tool descriptions
6. Run with `fastmcp dev main.py` and inspect in the MCP inspector
7. Call tools manually from the inspector UI

### Key concepts
- `FastMCP` server instantiation
- `@mcp.tool` decorator
- How Python types map to JSON Schema (`str`, `int`, `list`, `Literal`, `Optional`)
- Tool name, description, input schema — what the LLM actually sees
- `stdio` vs `http` transport

### Files touched
```
server/server.py
server/tools.py
main.py
```

---

## Phase 2 — Resources & Prompts

**Goal:** Understand the other two MCP primitives: resources (data) and prompts (templates).

### What you'll build
- A static resource (server info / help text)
- A dynamic resource (a simple in-memory note store)
- A templated resource URI (`note://notes/{id}`)
- Two prompt templates

### Steps
1. Add `server/resources.py` — define a static resource with `@mcp.resource`
2. Add an in-memory dict as a "notes" store
3. Expose notes as a resource template: `note://notes/{note_id}`
4. Add `server/prompts.py` — define prompts with `@mcp.prompt`
5. Understand the difference: tools *do things*, resources *expose data*, prompts *template messages*
6. Inspect all three types in `fastmcp dev`

### Key concepts
- `@mcp.resource` — static URI resources
- `@mcp.resource` with `{param}` — templated resource URIs
- `@mcp.prompt` — returning `list[Message]`
- Resource MIME types (`text/plain`, `application/json`)
- When to use a resource vs a tool

### Files touched
```
server/resources.py
server/prompts.py
server/server.py  (mount resources + prompts)
```

---

## Phase 3 — Context (Logging, Progress, Sampling)

**Goal:** Use the MCP `Context` object to communicate back to the client during tool execution.

### What you'll build
- A slow tool that reports progress (e.g. fake "processing" loop)
- Tools that log structured messages back to the client
- A tool that uses `ctx.sample()` to call an LLM mid-execution

### Steps
1. Inject `ctx: Context` into a tool function signature
2. Use `ctx.info()`, `ctx.warning()`, `ctx.error()` — see them appear in the inspector log
3. Use `ctx.report_progress(current, total)` — see the progress bar
4. Use `ctx.read_resource(uri)` inside a tool — tools calling resources
5. (Optional) Use `ctx.sample()` to make an LLM call from within a tool

### Key concepts
- `from fastmcp import Context`
- How `ctx` is injected automatically (not part of the tool's JSON schema)
- `ctx.log` vs `ctx.report_progress`
- Resource access from tool context
- LLM sampling from server side

### Files touched
```
server/tools.py   (add ctx to existing tools)
```

---

## Phase 4 — FastMCP Client

**Goal:** Drive an MCP server programmatically from Python, not just from Claude.

### What you'll build
A `client/client.py` script that connects to the server, lists tools, calls them, and reads resources.

### Steps
1. Create `client/client.py`
2. Connect using `FastMCP` client with stdio transport (point at `main.py`)
3. `await client.list_tools()` — print what the server exposes
4. `await client.call_tool("tool_name", {...})` — call a tool and print result
5. `await client.list_resources()` — list available resources
6. `await client.read_resource("note://notes/1")` — read a resource
7. `await client.get_prompt("prompt_name", {...})` — render a prompt
8. Try the `http` transport: run server separately, connect via URL

### Key concepts
- `from fastmcp import FastMCP` (client mode) vs server mode
- Transport types: `stdio`, `http`, `sse`
- `async with client:` context manager pattern
- Structured tool results vs raw text
- The difference between what Claude sees and what your Python code sees

### Files touched
```
client/client.py
```

---

## Phase 5 — Server Composition

**Goal:** Understand how large MCP setups are built from smaller servers.

### What you'll build
- Split tools into two sub-servers (e.g. `TextServer`, `MathServer`)
- Mount both into a single parent server
- Use a proxy to expose an external MCP server through yours

### Steps
1. Create `server/text_server.py` and `server/math_server.py` as standalone `FastMCP` instances
2. Mount them into the main server: `mcp.mount("text", text_server)`
3. Observe how tool names get namespaced: `text_tool_name`
4. Use `NamespaceTransform` to control prefixing
5. Create a `FastMCPProxy` that wraps an external server and re-exposes it
6. Combine proxy + local tools in one server

### Key concepts
- `server.mount(prefix, sub_server)` 
- Automatic namespace prefixing
- `FastMCPProxy` — proxying remote servers
- When to compose vs when to keep flat
- Tool name collisions and how to resolve them

### Files touched
```
server/text_server.py
server/math_server.py
server/server.py  (mount sub-servers)
```

---

## Phase 6 — Middleware

**Goal:** Add cross-cutting behavior to every request without touching tool logic.

### What you'll build
- A request/response logger middleware
- A timing middleware (how long each tool call takes)
- A rate limiter (limit calls per minute)
- A custom middleware from scratch

### Steps
1. Add FastMCP's built-in `LoggingMiddleware` to the server
2. Add `TimingMiddleware` — see tool execution time in logs
3. Add `RateLimitingMiddleware` with a per-minute cap
4. Write your own middleware class by subclassing `Middleware`
5. Chain multiple middlewares and observe ordering

### Key concepts
- `server.add_middleware(...)` 
- Middleware execution order (stack model)
- `call_next` — passing the request down the chain
- Middleware vs tool-level logic: what belongs where
- Built-in middlewares: logging, timing, rate limiting, error handling, caching

### Files touched
```
server/middleware.py  (custom middleware)
server/server.py      (register middlewares)
```

---

## Phase 7 — Authentication

**Goal:** Protect your server so only authorized clients can use it.

### What you'll build
- A server protected by a static bearer token
- Understand the OAuth 2.1 flow FastMCP supports
- Add a debug auth provider for local testing

### Steps
1. Switch server to HTTP transport (required for auth)
2. Add `BearerAuthProvider` with a hardcoded token
3. Try calling without a token — observe the 401
4. Add the token to the client — confirm it works
5. Add `DebugAuthProvider` for local dev (any token accepted)
6. Read how `OAuthProxy` works conceptually (don't need to implement fully)
7. Understand `AccessToken` and how to read user identity inside a tool

### Key concepts
- Why auth requires HTTP (not stdio)
- `BearerAuthProvider` — simplest real protection
- `DebugAuthProvider` — dev-only bypass
- `AccessToken` — what's in the token your tool receives
- OAuth 2.1 vs bearer-only: when you need each

### Files touched
```
server/server.py   (add auth provider)
client/client.py   (add bearer token to client)
```

---

## Phase 8 — Advanced Patterns

**Goal:** Go deep on the patterns that make production MCP servers powerful.

### 8a — Elicitation
Let a tool ask the user a question mid-execution and wait for the answer.
- Use `ctx.elicit()` to request structured input
- Build a tool that pauses and collects user data before continuing

### 8b — Tool Transforms
Reshape tools without rewriting them.
- Use `ToolTransform` to rename arguments
- Hide internal fields from the LLM's schema
- Add default values to an existing tool

### 8c — Tool Search
Replace a large flat tool list with on-demand search.
- Add `ToolSearchTransform` to the server
- Understand why this matters when you have 50+ tools

### 8d — Background Tasks
Run long operations without blocking.
- Use `ctx.run_task()` to start a background task
- Poll task status from the client

### 8e — Dependency Injection
Inject request-scoped values (DB connections, auth tokens) into tools cleanly.
- Use `get_context()` and `Annotated` deps
- Avoid global state in tools

### Files touched
```
server/tools.py       (elicitation, transforms, deps)
server/server.py      (transforms, task config)
client/client.py      (background task polling)
```

---

## Final Project Structure

After all phases, your codebase will look like:

```
PocketMCP/
├── main.py
├── ROADMAP.md
├── server/
│   ├── __init__.py
│   ├── server.py        # main server assembly + middleware + auth
│   ├── tools.py         # all tool definitions
│   ├── resources.py     # resource + resource template definitions
│   ├── prompts.py       # prompt templates
│   ├── text_server.py   # sub-server (Phase 5)
│   ├── math_server.py   # sub-server (Phase 5)
│   └── middleware.py    # custom middleware (Phase 6)
└── client/
    └── client.py        # programmatic client (Phase 4+)
```

---

## Quick Reference — Commands

```bash
# Run server in dev mode with inspector UI
fastmcp dev main.py

# Run server over HTTP
fastmcp run main.py --transport http --port 8000

# Inspect a running server's tools/resources
fastmcp inspect main.py

# Install server into Claude Desktop
fastmcp install main.py --name pocketmcp
```

---

## Checkpoints

Mark each phase done as you complete it.

- [ ] Phase 1 — Basic Server & Tools
- [ ] Phase 2 — Resources & Prompts
- [ ] Phase 3 — Context
- [ ] Phase 4 — FastMCP Client
- [ ] Phase 5 — Server Composition
- [ ] Phase 6 — Middleware
- [ ] Phase 7 — Authentication
- [ ] Phase 8 — Advanced Patterns
