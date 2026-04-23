async def test_forecast_subscription(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
    mock_google_weather_api: AsyncMock,
) -> None:
    """Test multiple forecast."""
    client = await hass_ws_client(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": "daily",
            "entity_id": "weather.home",
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

    assert forecast1 != []
    assert forecast1 == snapshot

    freezer.tick(timedelta(hours=1) + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    msg = await client.receive_json()

    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast2 = msg["event"]["forecast"]

    assert forecast2 != []
    assert forecast2 == snapshot