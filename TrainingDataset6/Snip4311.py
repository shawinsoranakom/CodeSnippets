async def test_raw_stream_cancellation() -> None:
    """Raw streaming endpoint should be cancellable within a reasonable time."""
    cancelled = await _run_asgi_and_cancel(app, "/stream-raw", timeout=3.0)
    # The key assertion: we reached this line at all (didn't hang).
    # cancelled will be True because the infinite generator was interrupted.
    assert cancelled