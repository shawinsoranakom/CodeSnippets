async def test_api_headers(
    aiohttp_raw_server,  # 'aiohttp_raw_server' must be before 'hass'!
    hass: HomeAssistant,
    api_call: str,
    method: Literal["GET", "POST"],
    payload: Any,
) -> None:
    """Test headers are forwarded correctly."""
    received_request = None

    async def mock_handler(request):
        """Return OK."""
        nonlocal received_request
        received_request = request
        return web.json_response({"result": "ok", "data": None})

    server = await aiohttp_raw_server(mock_handler)
    hassio_handler = HassIO(
        hass.loop,
        async_get_clientsession(hass),
        f"{server.host}:{server.port}",
    )

    await hassio_handler.send_command(api_call, method, payload)
    assert received_request is not None

    assert received_request.method == method
    assert received_request.headers.get("X-Hass-Source") == "core.handler"

    if method == "GET":
        assert hdrs.CONTENT_TYPE not in received_request.headers
        return

    assert hdrs.CONTENT_TYPE in received_request.headers
    if payload:
        assert received_request.headers[hdrs.CONTENT_TYPE] == "application/json"
    else:
        assert received_request.headers[hdrs.CONTENT_TYPE] == "application/octet-stream"