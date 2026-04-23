async def test_forecasts_invalid(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test invalid forecasts."""
    expected = {TEST_WEATHER.entity_id: {"forecast": []}}

    # Test valid keys
    hass.states.async_set(
        "sensor.forecast_daily",
        "sunny",
        {
            ATTR_FORECAST: [
                Forecast(
                    condition="cloudy",
                    datetime="2023-02-17T14:00:00+00:00",
                    temperature=14.2,
                    not_correct=1,
                )
            ]
        },
    )
    hass.states.async_set(
        "sensor.forecast_hourly",
        "sunny",
        {ATTR_FORECAST: None},
    )
    await hass.async_block_till_done()
    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {"entity_id": TEST_WEATHER.entity_id, "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    assert response == expected

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {"entity_id": TEST_WEATHER.entity_id, "type": "daily"},
        blocking=True,
        return_response=True,
    )
    assert response == expected
    assert "expected valid forecast keys, unallowed keys:" in caplog.text

    # Test twice daily missing is_daytime
    hass.states.async_set(
        "sensor.forecast_twice_daily",
        "sunny",
        {
            ATTR_FORECAST: [
                Forecast(
                    condition="cloudy",
                    datetime="2023-02-17T14:00:00+00:00",
                    temperature=14.2,
                )
            ]
        },
    )
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {"entity_id": TEST_WEATHER.entity_id, "type": "twice_daily"},
        blocking=True,
        return_response=True,
    )
    assert response == expected
    assert "`is_daytime` is missing in twice_daily forecast" in caplog.text

    # Test twice daily missing datetime
    hass.states.async_set(
        "sensor.forecast_twice_daily",
        "sunny",
        {
            ATTR_FORECAST: [
                Forecast(
                    condition="cloudy",
                    temperature=14.2,
                    is_daytime=True,
                )
            ]
        },
    )
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {"entity_id": TEST_WEATHER.entity_id, "type": "twice_daily"},
        blocking=True,
        return_response=True,
    )
    assert response == expected
    assert "`datetime` is missing in forecast" in caplog.text