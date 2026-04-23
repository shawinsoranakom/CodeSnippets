async def test_camera_web_rtc(
    hass: HomeAssistant,
    auth,
    hass_ws_client: WebSocketGenerator,
    setup_platform,
) -> None:
    """Test a basic camera that supports web rtc."""
    expiration = utcnow() + datetime.timedelta(seconds=100)
    auth.responses = [
        aiohttp.web.json_response(
            {
                "results": {
                    "answerSdp": "v=0\r\ns=-\r\n",
                    "mediaSessionId": "yP2grqz0Y1V_wgiX9KEbMWHoLd...",
                    "expiresAt": expiration.isoformat(timespec="seconds"),
                },
            }
        )
    ]
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING
    client = await hass_ws_client(hass)
    assert await async_frontend_stream_types(client, "camera.my_camera") == [
        StreamType.WEB_RTC
    ]

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.my_camera",
            "offer": "a=recvonly",
        }
    )

    response = await client.receive_json()
    assert response["type"] == TYPE_RESULT
    assert response["success"]
    subscription_id = response["id"]

    # Session id
    response = await client.receive_json()
    assert response["id"] == subscription_id
    assert response["type"] == "event"
    assert response["event"]["type"] == "session"

    # Answer
    response = await client.receive_json()
    assert response["id"] == subscription_id
    assert response["type"] == "event"
    assert response["event"] == {
        "type": "answer",
        "answer": "v=0\r\ns=-\r\n",
    }

    # Nest WebRTC cameras return a placeholder
    await async_get_image(hass)
    await async_get_image(hass, width=1024, height=768)