async def test_forecast_subscription(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    mock_weather,
    snapshot: SnapshotAssertion,
    forecast_type: str,
) -> None:
    """Test multiple forecast."""
    client = await hass_ws_client(hass)

    mock_weather.get_forecast.return_value = [
        {
            "condition": "SleetSunThunder",
            "datetime": datetime.datetime(2023, 8, 8, 12, 0, tzinfo=datetime.UTC),
            "temperature": 10.0,
        },
        {
            "condition": "SleetSunThunder",
            "datetime": datetime.datetime(2023, 8, 9, 12, 0, tzinfo=datetime.UTC),
            "temperature": 20.0,
        },
    ]

    await setup_config_entry(hass)
    assert len(hass.states.async_entity_ids("weather")) == 1
    entity_id = hass.states.async_entity_ids("weather")[0]

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

    assert forecast1 == snapshot

    mock_weather.get_forecast.return_value = [
        {
            "condition": "SleetSunThunder",
            "datetime": datetime.datetime(2023, 8, 8, 12, 0, tzinfo=datetime.UTC),
            "temperature": 15.0,
        },
        {
            "condition": "SleetSunThunder",
            "datetime": datetime.datetime(2023, 8, 9, 12, 0, tzinfo=datetime.UTC),
            "temperature": 25.0,
        },
    ]

    freezer.tick(UPDATE_INTERVAL + datetime.timedelta(seconds=1))
    await hass.async_block_till_done()
    msg = await client.receive_json()

    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast2 = msg["event"]["forecast"]

    assert forecast2 == snapshot