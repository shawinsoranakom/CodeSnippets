async def test_forecast_subscription(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
    forecast_type: str,
) -> None:
    """Test multiple forecast."""
    client = await hass_ws_client(hass)

    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        entry = MockConfigEntry(domain="ipma", data=TEST_CONFIG)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": forecast_type,
            "entity_id": "weather.hometown",
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

    assert forecast1 == snapshot

    freezer.tick(MIN_TIME_BETWEEN_UPDATES + datetime.timedelta(seconds=1))
    await hass.async_block_till_done()
    msg = await client.receive_json()

    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast2 = msg["event"]["forecast"]

    assert forecast2 == snapshot