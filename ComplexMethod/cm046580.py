def _resolve_local_v1_endpoint(request: Request) -> str:
    """Return the loopback /v1 URL for the actual backend listen port.

    Resolution order:
      1. ``app.state.server_port`` - explicitly published by run.py after
         the uvicorn server has bound. This is the most reliable source
         because it survives reverse proxies, TLS terminators and tunnels.
      2. ``request.scope["server"]`` - the real (host, port) tuple uvicorn
         sets when the request is dispatched. Used when Studio is started
         outside ``run_server`` (e.g. ``uvicorn studio.backend.main:app``).
      3. ``request.base_url`` parsed - last resort for test fixtures that
         do not route through a live uvicorn server.
    """
    port: Any = getattr(request.app.state, "server_port", None)
    if not isinstance(port, int) or port <= 0:
        server = request.scope.get("server")
        if (
            isinstance(server, tuple)
            and len(server) >= 2
            and isinstance(server[1], int)
            and server[1] > 0
        ):
            port = server[1]
        else:
            parsed = urlparse(str(request.base_url))
            port = parsed.port if parsed.port is not None else 8888
    return f"http://127.0.0.1:{int(port)}/v1"