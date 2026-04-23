async def test_ffmpeg_error_stderr_truncated(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that ffmpeg stderr output is truncated in error logs."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    total_lines = _MAX_STDERR_LINES + 50
    stderr_lines_data = [f"stderr line {i}\n".encode() for i in range(total_lines)] + [
        b""
    ]

    async def _stdout_read(_size: int = -1) -> bytes:
        """Yield to event loop so stderr collector can run, then return EOF."""
        await asyncio.sleep(0)
        return b""

    mock_proc = AsyncMock()
    mock_proc.stdout.read = _stdout_read
    mock_proc.stderr.readline = AsyncMock(side_effect=stderr_lines_data)
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        url = async_create_proxy_url(hass, device_id, "dummy-input", media_format="mp3")
        req = await client.get(url)
        assert req.status == HTTPStatus.OK
        await req.content.read()

    # Should log an error with stderr content
    assert "FFmpeg conversion failed for device" in caplog.text

    # Find the error message to verify truncation.
    # We can't just check caplog.text because lines beyond the limit
    # are still present at debug level from _collect_ffmpeg_stderr.
    error_message = next(
        r.message
        for r in caplog.records
        if r.levelno >= logging.ERROR and "FFmpeg conversion failed" in r.message
    )

    total_lines = _MAX_STDERR_LINES + 50

    # The last _MAX_STDERR_LINES lines should be present
    for i in range(total_lines - _MAX_STDERR_LINES, total_lines):
        assert f"stderr line {i}" in error_message

    # Early lines that were evicted should not be in the error log
    assert "stderr line 0" not in error_message