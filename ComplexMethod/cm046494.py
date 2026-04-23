def run_server(
    host: str = "0.0.0.0",
    port: int = 8888,
    frontend_path: Path = Path(__file__).resolve().parent.parent / "frontend" / "dist",
    silent: bool = False,
    llama_parallel_slots: int = 1,
):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to (auto-increments if in use)
        frontend_path: Path to frontend build directory (optional)
        silent: Suppress startup messages
        llama_parallel_slots: Number of parallel slots for llama-server

    Note:
        Signal handlers are NOT registered here so that embedders
        (e.g. Colab notebooks) keep their own interrupt semantics.
        Standalone callers should register handlers after calling this.
    """
    global _server, _shutdown_event

    # On Windows the default console encoding (cp1252) cannot encode emoji.
    # Reconfigure stdout to UTF-8 so startup messages do not crash the server.
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding = "utf-8", errors = "replace")
        except Exception:
            pass

    import nest_asyncio

    nest_asyncio.apply()

    import asyncio
    from threading import Thread, Event
    import time
    import uvicorn

    from main import app, setup_frontend
    from utils.paths import ensure_studio_directories

    # Create all standard directories on startup
    ensure_studio_directories()

    # Auto-find free port if requested port is in use
    if not _is_port_free(host, port):
        original_port = port
        blocker = _get_pid_on_port(port)
        port = _find_free_port(host, port + 1)
        if not silent:
            print("")
            print("=" * 50)
            if blocker:
                pid, name = blocker
                print(
                    f"Port {original_port} is already in use by " f"{name} (PID {pid})."
                )
            else:
                print(f"Port {original_port} is already in use.")
            print(f"Unsloth Studio will use port {port} instead.")
            print(f"Open http://localhost:{port} in your browser.")
            print("=" * 50)
            print("")

    # Setup frontend if path provided
    if frontend_path:
        if setup_frontend(app, frontend_path):
            if not silent:
                print(f"[OK] Frontend loaded from {frontend_path}")
        else:
            if not silent:
                print(f"[WARNING] Frontend not found at {frontend_path}")

    # Create the uvicorn server and expose it for signal handlers
    config = uvicorn.Config(
        app, host = host, port = port, log_level = "info", access_log = False
    )
    _server = uvicorn.Server(config)
    _shutdown_event = Event()

    # Expose the actual bound port so request-handling code can build
    # loopback URLs that point at the real backend, not whatever port a
    # reverse proxy or tunnel exposed in the request URL. Only publish
    # an explicit value when we know the concrete port; for ephemeral
    # binds (port==0) leave it unset and let request handlers fall back
    # to the ASGI request scope or request.base_url.
    app.state.server_port = port if port and port > 0 else None
    app.state.llama_parallel_slots = llama_parallel_slots

    # Run server in a daemon thread
    def _run():
        asyncio.run(_server.serve())

    thread = Thread(target = _run, daemon = True)
    thread.start()
    time.sleep(3)

    _write_pid_file()
    import atexit

    atexit.register(_remove_pid_file)

    # Expose a shutdown callable via app.state so the /api/shutdown endpoint
    # can trigger graceful shutdown without circular imports.
    def _trigger_shutdown():
        _graceful_shutdown(_server)
        if _shutdown_event is not None:
            _shutdown_event.set()

    app.state.trigger_shutdown = _trigger_shutdown

    if not silent:
        display_host = _resolve_external_ip() if host == "0.0.0.0" else host
        print_studio_access_banner(
            port = port,
            bind_host = host,
            display_host = display_host,
        )

    return app