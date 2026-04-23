async def _run_asgi_and_cancel(app: FastAPI, path: str, timeout: float) -> bool:
    """Call the ASGI app for *path* and cancel after *timeout* seconds.

    Returns `True` if the cancellation was delivered (i.e. it did not hang).
    """
    chunks: list[bytes] = []

    async def receive():  # type: ignore[no-untyped-def]
        # Simulate a client that never disconnects, rely on cancellation
        await anyio.sleep(float("inf"))
        return {"type": "http.disconnect"}  # pragma: no cover

    async def send(message: dict) -> None:  # type: ignore[type-arg]
        if message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "server": ("test", 80),
    }

    with anyio.move_on_after(timeout) as cancel_scope:
        await app(scope, receive, send)  # type: ignore[arg-type]

    # If we got here within the timeout the generator was cancellable.
    # cancel_scope.cancelled_caught is True when move_on_after fired.
    return cancel_scope.cancelled_caught or len(chunks) > 0