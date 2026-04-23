async def test_forecast_services(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    load_int: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test multiple forecast."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": "daily",
            "entity_id": ENTITY_ID,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast1 = msg["event"]["forecast"]

    assert len(forecast1) == 11
    assert forecast1[0] == snapshot
    assert forecast1[6] == snapshot

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": "hourly",
            "entity_id": ENTITY_ID,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast1 = msg["event"]["forecast"]

    assert len(forecast1) == 59
    assert forecast1[0] == snapshot
    assert forecast1[6] == snapshot