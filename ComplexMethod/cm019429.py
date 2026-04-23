async def test_websocket_webrtc_offer(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test initiating a WebRTC stream with offer and answer."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.async",
            "offer": WEBRTC_OFFER,
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
        "answer": WEBRTC_ANSWER,
    }

    # Unsubscribe/Close session
    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": subscription_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]