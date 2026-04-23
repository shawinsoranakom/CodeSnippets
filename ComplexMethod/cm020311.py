async def test_camera_web_rtc_offer_failure(
    hass: HomeAssistant,
    auth,
    hass_ws_client: WebSocketGenerator,
    setup_platform,
) -> None:
    """Test a basic camera that supports web rtc."""
    auth.responses = [
        aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST),
    ]
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

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
        "type": "error",
        "code": "webrtc_offer_failed",
        "message": "Nest API error:  response from API (400)",
    }