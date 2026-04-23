async def test_ffmpeg_error_redacts_sensitive_urls(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that sensitive query params are redacted in error logs."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    sensitive_url = (
        "https://example.com/api/tts?authSig=secret123&token=abc456&other=keep"
    )
    stderr_lines_data = [
        f"Error opening input file {sensitive_url}\n".encode(),
        b"",
    ]

    async def _stdout_read(_size: int = -1) -> bytes:
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

    error_message = next(
        r.message
        for r in caplog.records
        if r.levelno >= logging.ERROR and "FFmpeg conversion failed" in r.message
    )

    assert "authSig=REDACTED" in error_message
    assert "token=REDACTED" in error_message
    assert "secret123" not in error_message
    assert "abc456" not in error_message
    assert "other=keep" in error_message