async def test_general_forecast_sensor(
    hass: HomeAssistant, general_channel_config_entry: MockConfigEntry
) -> None:
    """Test the General Forecast sensor."""
    await setup_integration(hass, general_channel_config_entry)
    assert len(hass.states.async_all()) == 6
    price = hass.states.get("sensor.mock_title_general_forecast")
    assert price
    assert price.state == "0.09"
    attributes = price.attributes
    assert attributes["channel_type"] == "general"
    assert attributes["attribution"] == "Data provided by Amber Electric"

    first_forecast = attributes["forecasts"][0]
    assert first_forecast["duration"] == 30
    assert first_forecast["date"] == "2021-09-21"
    assert first_forecast["per_kwh"] == 0.09
    assert first_forecast["nem_date"] == "2021-09-21T09:00:00+10:00"
    assert first_forecast["spot_per_kwh"] == 0.01
    assert first_forecast["start_time"] == "2021-09-21T08:30:00+10:00"
    assert first_forecast["end_time"] == "2021-09-21T09:00:00+10:00"
    assert first_forecast["renewables"] == 50
    assert first_forecast["spike_status"] == "none"
    assert first_forecast["descriptor"] == "very_low"

    assert first_forecast.get("range_min") is None
    assert first_forecast.get("range_max") is None