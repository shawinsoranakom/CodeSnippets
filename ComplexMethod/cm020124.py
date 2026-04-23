async def test_ws_subscription(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test websocket subscription."""
    assert await async_setup_component(hass, "hassio", {})
    client = await hass_ws_client(hass)
    await client.send_json({WS_ID: 5, WS_TYPE: WS_TYPE_SUBSCRIBE})
    response = await client.receive_json()
    assert response["success"]

    calls = async_mock_signal(hass, EVENT_SUPERVISOR_EVENT)
    async_dispatcher_send(hass, EVENT_SUPERVISOR_EVENT, {"lorem": "ipsum"})

    response = await client.receive_json()
    assert response["event"]["lorem"] == "ipsum"
    assert len(calls) == 1

    await client.send_json(
        {
            WS_ID: 6,
            WS_TYPE: "supervisor/event",
            ATTR_DATA: {ATTR_WS_EVENT: "test", "lorem": "ipsum"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert len(calls) == 2

    response = await client.receive_json()
    assert response["event"]["lorem"] == "ipsum"

    # Unsubscribe
    await client.send_json({WS_ID: 7, WS_TYPE: "unsubscribe_events", "subscription": 5})
    response = await client.receive_json()
    assert response["success"]