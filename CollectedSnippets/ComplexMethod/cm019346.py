async def test_subscribe_forecast(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_flow_fixture: None,
) -> None:
    """Test multiple forecast."""

    class MockWeatherMockForecast(MockWeatherTest):
        """Mock weather class."""

        async def async_forecast_daily(self) -> list[Forecast] | None:
            """Return the forecast_daily."""
            return self.forecast_list

    kwargs = {
        "native_temperature": 38,
        "native_temperature_unit": UnitOfTemperature.CELSIUS,
        "supported_features": WeatherEntityFeature.FORECAST_DAILY,
    }
    weather_entity = await create_entity(hass, MockWeatherMockForecast, None, **kwargs)

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "weather/subscribe_forecast",
            "forecast_type": "daily",
            "entity_id": weather_entity.entity_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    forecast = msg["event"]
    assert forecast == {
        "type": "daily",
        "forecast": [
            {
                "cloud_coverage": None,
                "temperature": 38.0,
                "templow": 38.0,
                "uv_index": None,
                "wind_bearing": None,
            }
        ],
    }

    await weather_entity.async_update_listeners(None)
    msg = await client.receive_json()
    assert msg["event"] == forecast

    await weather_entity.async_update_listeners(["daily"])
    msg = await client.receive_json()
    assert msg["event"] == forecast

    weather_entity.forecast_list = None
    await weather_entity.async_update_listeners(None)
    msg = await client.receive_json()
    assert msg["event"] == {"type": "daily", "forecast": None}