async def test_general_price_sensor(
    hass: HomeAssistant, general_channel_config_entry: MockConfigEntry
) -> None:
    """Test the General Price sensor."""
    await setup_integration(hass, general_channel_config_entry)
    assert len(hass.states.async_all()) == 6
    price = hass.states.get("sensor.mock_title_general_price")
    assert price
    assert price.state == "0.09"
    attributes = price.attributes
    assert attributes["duration"] == 30
    assert attributes["date"] == "2021-09-21"
    assert attributes["per_kwh"] == 0.09
    assert attributes["nem_date"] == "2021-09-21T08:30:00+10:00"
    assert attributes["spot_per_kwh"] == 0.01
    assert attributes["start_time"] == "2021-09-21T08:00:00+10:00"
    assert attributes["end_time"] == "2021-09-21T08:30:00+10:00"
    assert attributes["renewables"] == 51
    assert attributes["estimate"] is True
    assert attributes["spike_status"] == "none"
    assert attributes["channel_type"] == "general"
    assert attributes["attribution"] == "Data provided by Amber Electric"
    assert attributes.get("range_min") is None
    assert attributes.get("range_max") is None