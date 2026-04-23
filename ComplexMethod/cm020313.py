async def test_webrtc_refresh_expired_stream(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    hass_ws_client: WebSocketGenerator,
    auth: FakeAuth,
) -> None:
    """Test a camera webrtc expiration and refresh."""
    now = utcnow()

    stream_1_expiration = now + datetime.timedelta(seconds=90)
    stream_2_expiration = now + datetime.timedelta(seconds=180)
    auth.responses = [
        aiohttp.web.json_response(
            {
                "results": {
                    "answerSdp": "v=0\r\ns=-\r\n",
                    "mediaSessionId": "yP2grqz0Y1V_wgiX9KEbMWHoLd...",
                    "expiresAt": stream_1_expiration.isoformat(timespec="seconds"),
                },
            }
        ),
        aiohttp.web.json_response(
            {
                "results": {
                    "mediaSessionId": "yP2grqz0Y1V_wgiX9KEbMWHoLd...",
                    "expiresAt": stream_2_expiration.isoformat(timespec="seconds"),
                },
            }
        ),
    ]
    await setup_platform()
    await hass.async_block_till_done()

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

    assert len(auth.captured_requests) == 1
    assert (
        auth.captured_requests[0][2].get("command")
        == "sdm.devices.commands.CameraLiveStream.GenerateWebRtcStream"
    )

    # Fire alarm before stream_1_expiration. The stream url is not refreshed
    next_update = now + datetime.timedelta(seconds=25)
    await fire_alarm(hass, next_update)
    assert len(auth.captured_requests) == 1

    # Alarm is near stream_1_expiration which causes the stream extension
    next_update = now + datetime.timedelta(seconds=60)
    await fire_alarm(hass, next_update)

    assert len(auth.captured_requests) >= 2
    assert (
        auth.captured_requests[1][2].get("command")
        == "sdm.devices.commands.CameraLiveStream.ExtendWebRtcStream"
    )