async def test_failed_get_observation_forecast(hass: HomeAssistant) -> None:
    """Test for successfully setting up the IPMA platform."""
    with patch(
        "pyipma.location.Location.get",
        return_value=MockBadLocation(),
    ):
        entry = MockConfigEntry(domain="ipma", data=TEST_CONFIG)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("weather.hometown")
    assert state.state == STATE_UNKNOWN

    data = state.attributes
    assert data.get(ATTR_WEATHER_TEMPERATURE) is None
    assert data.get(ATTR_WEATHER_HUMIDITY) is None
    assert data.get(ATTR_WEATHER_PRESSURE) is None
    assert data.get(ATTR_WEATHER_WIND_SPEED) is None
    assert data.get(ATTR_WEATHER_WIND_BEARING) is None
    assert state.attributes.get("friendly_name") == "HomeTown"