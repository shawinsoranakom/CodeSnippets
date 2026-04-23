async def test_camera_web_rtc_unsupported(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_platform,
) -> None:
    """Test a basic camera that supports web rtc."""
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

    client = await hass_ws_client(hass)
    assert await async_frontend_stream_types(client, "camera.my_camera") == [
        StreamType.HLS
    ]

    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.my_camera",
            "offer": "a=recvonly",
        }
    )

    msg = await client.receive_json()
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]
    assert msg["error"] == {
        "code": "webrtc_offer_failed",
        "message": "Camera does not support WebRTC, frontend_stream_types={<StreamType.HLS: 'hls'>}",
    }