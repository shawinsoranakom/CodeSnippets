async def test_camera_ws_stream(
    hass: HomeAssistant,
    setup_platform,
    camera_device,
    hass_ws_client: WebSocketGenerator,
    auth,
    mock_create_stream,
) -> None:
    """Test a basic camera that supports web rtc."""
    auth.responses = [make_stream_url_response()]
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING
    client = await hass_ws_client(hass)
    frontend_stream_types = await async_frontend_stream_types(
        client, "camera.my_camera"
    )
    assert frontend_stream_types == [StreamType.HLS]

    await client.send_json(
        {
            "id": 2,
            "type": "camera/stream",
            "entity_id": "camera.my_camera",
        }
    )
    msg = await client.receive_json()

    assert msg["id"] == 2
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["url"] == "http://home.assistant/playlist.m3u8"