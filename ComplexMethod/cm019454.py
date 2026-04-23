async def test_forecast_subscription(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
    mock_simple_nws,
    no_sensor,
    forecast_type: str,
    entity_id: str,
) -> None:
    """Test multiple forecast."""
    client = await hass_ws_client(hass)

    # Pre-create the hourly entity
    entity_registry.async_get_or_create(
        WEATHER_DOMAIN,
        nws.DOMAIN,
        "35_-75_hourly",
        suggested_object_id="abc_hourly",
    )

    entry = MockConfigEntry(
        domain=nws.DOMAIN,
        data=NWS_CONFIG,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": forecast_type,
            "entity_id": entity_id,
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

    freezer.tick(nws.DEFAULT_SCAN_INTERVAL + timedelta(seconds=1))
    await hass.async_block_till_done()
    msg = await client.receive_json()

    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast2 = msg["event"]["forecast"]

    assert forecast2 != []
    assert forecast2 == snapshot