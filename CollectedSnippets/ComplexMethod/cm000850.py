async def test_disconnect_all_listeners_cancels_matching_session():
    task_a = asyncio.create_task(_sleep_forever())
    task_b = asyncio.create_task(_sleep_forever())
    task_other = asyncio.create_task(_sleep_forever())

    stream_registry._listener_sessions[1] = ("sess-1", task_a)
    stream_registry._listener_sessions[2] = ("sess-1", task_b)
    stream_registry._listener_sessions[3] = ("sess-other", task_other)

    try:
        cancelled = await stream_registry.disconnect_all_listeners("sess-1")

        assert cancelled == 2
        assert task_a.cancelled()
        assert task_b.cancelled()
        assert not task_other.done()
        # Matching entries are removed, non-matching entries remain.
        assert 1 not in stream_registry._listener_sessions
        assert 2 not in stream_registry._listener_sessions
        assert 3 in stream_registry._listener_sessions
    finally:
        task_other.cancel()
        try:
            await task_other
        except asyncio.CancelledError:
            pass