def _get_websocket_headers() -> Optional[Dict[str, str]]:
    """Return a copy of the HTTP request headers for the current session's
    WebSocket connection. If there's no active session, return None instead.

    Raise an error if the server is not running.

    Note to the intrepid: this is an UNSUPPORTED, INTERNAL API. (We don't have plans
    to remove it without a replacement, but we don't consider this a production-ready
    function, and its signature may change without a deprecation warning.)
    """
    ctx = get_script_run_ctx()
    if ctx is None:
        return None

    session_client = runtime.get_instance().get_client(ctx.session_id)
    if session_client is None:
        return None

    if not isinstance(session_client, BrowserWebSocketHandler):
        raise RuntimeError(
            f"SessionClient is not a BrowserWebSocketHandler! ({session_client})"
        )

    return dict(session_client.request.headers)