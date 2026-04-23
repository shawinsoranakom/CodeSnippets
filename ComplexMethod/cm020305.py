async def test_camera_ws_stream_failure(
    hass: HomeAssistant,
    setup_platform,
    camera_device,
    hass_ws_client: WebSocketGenerator,
    auth,
) -> None:
    """Test a basic camera that supports web rtc."""
    auth.responses = [aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST)]
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 3,
            "type": "camera/stream",
            "entity_id": "camera.my_camera",
        }
    )

    msg = await client.receive_json()
    assert msg["id"] == 3
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "start_stream_failed"
    assert msg["error"]["message"].startswith("Nest API error")