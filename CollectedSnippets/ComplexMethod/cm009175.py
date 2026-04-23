async def test_astream_with_chunk_timeout_logs_on_fire(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Structured log carries source + timeout_s for aggregate-log filtering."""
    # Pin the logger + level; don't rely on caplog's default or module
    # inheritance so the test can't silently no-op.
    caplog.set_level(
        logging.WARNING, logger="langchain_openai.chat_models._client_utils"
    )

    source = _FakeSource(["a"], per_item_sleep=0.2)
    with pytest.raises(StreamChunkTimeoutError):
        async for _ in _astream_with_chunk_timeout(source, 0.05):
            pass

    records = [
        r
        for r in caplog.records
        if r.name == "langchain_openai.chat_models._client_utils"
        and getattr(r, "source", None) == "stream_chunk_timeout"
    ]
    assert len(records) == 1, f"expected one structured record, got {len(records)}"
    record = records[0]
    assert record.levelno == logging.WARNING
    assert record.__dict__["timeout_s"] == 0.05