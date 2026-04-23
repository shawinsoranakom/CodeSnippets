async def test_camera_multiple_streams(
    hass: HomeAssistant,
    auth,
    hass_ws_client: WebSocketGenerator,
    create_device,
    setup_platform,
) -> None:
    """Test a camera supporting multiple stream types."""
    expiration = utcnow() + datetime.timedelta(seconds=100)
    auth.responses = [
        # WebRTC response
        aiohttp.web.json_response(
            {
                "results": {
                    "answerSdp": "v=0\r\ns=-\r\n",
                    "mediaSessionId": "yP2grqz0Y1V_wgiX9KEbMWHoLd...",
                    "expiresAt": expiration.isoformat(timespec="seconds"),
                },
            }
        ),
    ]
    create_device.create(
        {
            "sdm.devices.traits.Info": {
                "customName": "My Camera",
            },
            "sdm.devices.traits.CameraLiveStream": {
                "maxVideoResolution": {
                    "width": 640,
                    "height": 480,
                },
                "videoCodecs": ["H264"],
                "audioCodecs": ["AAC"],
                "supportedProtocols": ["WEB_RTC", "RTSP"],
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING
    # Prefer WebRTC over RTSP/HLS
    client = await hass_ws_client(hass)
    assert await async_frontend_stream_types(client, "camera.my_camera") == [
        StreamType.WEB_RTC
    ]

    # RTSP stream is not supported
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert not stream_source

    # WebRTC stream
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