def main(base_url, host, port, mode, api_key, transport_sse_enabled, transport_streamable_http_enabled, json_response):
    import os

    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    def parse_bool_flag(key: str, default: bool) -> bool:
        val = os.environ.get(key, str(default))
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    global BASE_URL, HOST, PORT, MODE, HOST_API_KEY, TRANSPORT_SSE_ENABLED, TRANSPORT_STREAMABLE_HTTP_ENABLED, JSON_RESPONSE
    BASE_URL = os.environ.get("RAGFLOW_MCP_BASE_URL", base_url)
    HOST = os.environ.get("RAGFLOW_MCP_HOST", host)
    PORT = os.environ.get("RAGFLOW_MCP_PORT", str(port))
    MODE = os.environ.get("RAGFLOW_MCP_LAUNCH_MODE", mode)
    HOST_API_KEY = os.environ.get("RAGFLOW_MCP_HOST_API_KEY", api_key)
    TRANSPORT_SSE_ENABLED = parse_bool_flag("RAGFLOW_MCP_TRANSPORT_SSE_ENABLED", transport_sse_enabled)
    TRANSPORT_STREAMABLE_HTTP_ENABLED = parse_bool_flag("RAGFLOW_MCP_TRANSPORT_STREAMABLE_ENABLED", transport_streamable_http_enabled)
    JSON_RESPONSE = parse_bool_flag("RAGFLOW_MCP_JSON_RESPONSE", json_response)

    if MODE == LaunchMode.SELF_HOST and not HOST_API_KEY:
        raise click.UsageError("--api-key is required when --mode is 'self-host'")

    if not TRANSPORT_STREAMABLE_HTTP_ENABLED and JSON_RESPONSE:
        JSON_RESPONSE = False

    print(
        r"""
__  __  ____ ____       ____  _____ ______     _______ ____
|  \/  |/ ___|  _ \     / ___|| ____|  _ \ \   / / ____|  _ \
| |\/| | |   | |_) |    \___ \|  _| | |_) \ \ / /|  _| | |_) |
| |  | | |___|  __/      ___) | |___|  _ < \ V / | |___|  _ <
|_|  |_|\____|_|        |____/|_____|_| \_\ \_/  |_____|_| \_\
        """,
        flush=True,
    )
    print(f"MCP launch mode: {MODE}", flush=True)
    print(f"MCP host: {HOST}", flush=True)
    print(f"MCP port: {PORT}", flush=True)
    print(f"MCP base_url: {BASE_URL}", flush=True)

    if not any([TRANSPORT_SSE_ENABLED, TRANSPORT_STREAMABLE_HTTP_ENABLED]):
        print("At least one transport should be enabled, enable streamable-http automatically", flush=True)
        TRANSPORT_STREAMABLE_HTTP_ENABLED = True

    if TRANSPORT_SSE_ENABLED:
        print("SSE transport enabled: yes", flush=True)
        print("SSE endpoint available at /sse", flush=True)
    else:
        print("SSE transport enabled: no", flush=True)

    if TRANSPORT_STREAMABLE_HTTP_ENABLED:
        print("Streamable HTTP transport enabled: yes", flush=True)
        print("Streamable HTTP endpoint available at /mcp", flush=True)
        if JSON_RESPONSE:
            print("Streamable HTTP mode: JSON response enabled", flush=True)
        else:
            print("Streamable HTTP mode: SSE over HTTP enabled", flush=True)
    else:
        print("Streamable HTTP transport enabled: no", flush=True)
        if JSON_RESPONSE:
            print("Warning: --json-response ignored because streamable transport is disabled.", flush=True)

    uvicorn.run(
        create_starlette_app(),
        host=HOST,
        port=int(PORT),
    )