async def test_forecast(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    weather_only: None,
    forecast_type: str,
    expected_forecast: list[dict[str, Any]],
) -> None:
    """Test multiple forecast."""
    assert await async_setup_component(
        hass, weather.DOMAIN, {"weather": {"platform": "demo"}}
    )
    hass.config.units = METRIC_SYSTEM
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": forecast_type,
            "entity_id": "weather.demo_weather_north",
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

    assert len(forecast1) == 7
    for key, val in expected_forecast[0].items():
        assert forecast1[0][key] == val
    for key, val in expected_forecast[1].items():
        assert forecast1[6][key] == val

    freezer.tick(WEATHER_UPDATE_INTERVAL + datetime.timedelta(seconds=1))
    await hass.async_block_till_done()

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast2 = msg["event"]["forecast"]

    assert forecast2 != forecast1
    assert len(forecast2) == 7