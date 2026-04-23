async def test_coordinator_updates(
    hass: HomeAssistant,
    mock_incomfort: MagicMock,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test the incomfort coordinator is updating."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    state = hass.states.get("climate.thermostat_1")
    assert state is not None
    assert state.attributes["current_temperature"] == 21.4
    mock_incomfort().mock_room_status["room_temp"] = 20.91

    state = hass.states.get("sensor.boiler_pressure")
    assert state is not None
    assert state.state == "1.86"
    mock_incomfort().mock_heater_status["pressure"] = 1.84

    freezer.tick(timedelta(seconds=UPDATE_INTERVAL + 5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("climate.thermostat_1")
    assert state is not None
    assert state.attributes["current_temperature"] == 20.9

    state = hass.states.get("sensor.boiler_pressure")
    assert state is not None
    assert state.state == "1.84"