def _warn_if_proxy_env_shadowed(
    socket_options: tuple[SocketOption, ...],
    *,
    openai_proxy: str | None,
) -> None:
    """Warn once if a custom transport will shadow httpx's proxy auto-detection.

    When `socket_options` is non-empty we pass a custom `httpx` transport,
    which disables httpx's native proxy auto-detection — both the uppercase
    `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` env vars and their lowercase
    equivalents, plus macOS/Windows system proxy config. If the user
    supplies `openai_proxy` explicitly we route through it and the env-var
    handling is moot. Otherwise, a user whose app was transparently relying
    on any of those sources will silently stop using them on upgrade —
    emit a single WARNING so the behavior change is discoverable.

    Detection uses `urllib.request.getproxies()` — the same surface httpx
    reads — so lowercase env vars and macOS/Windows system proxy settings
    are caught alongside the uppercase names.
    """
    global _proxy_env_warning_emitted
    if _proxy_env_warning_emitted or not socket_options or openai_proxy:
        return
    active = [name for name in _PROXY_ENV_VARS if os.environ.get(name)]
    try:
        detected = bool(urllib.request.getproxies())
    except Exception:
        detected = False
    if not active and not detected:
        return
    _proxy_env_warning_emitted = True
    if active:
        source = ", ".join(active) + " set in environment"
    else:
        source = "system proxy configuration detected"
    logger.warning(
        "langchain-openai injected a custom httpx transport to apply "
        "`http_socket_options`, which disables httpx's proxy "
        "auto-detection (%s). Set "
        "`LANGCHAIN_OPENAI_TCP_KEEPALIVE=0` or pass `http_socket_options=()` "
        "to restore default proxy behavior, or supply `openai_proxy` / your "
        "own `http_client` / `http_async_client` to take full control.",
        source,
    )