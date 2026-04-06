async def test_jsonl_stream_cancellation() -> None:
    """JSONL streaming endpoint should be cancellable within a reasonable time."""
    cancelled = await _run_asgi_and_cancel(app, "/stream-jsonl", timeout=3.0)
    assert cancelled