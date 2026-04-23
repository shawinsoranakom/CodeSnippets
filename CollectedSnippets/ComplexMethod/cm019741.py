async def test_vehicle_refresh_token_expired_recovery(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
    mock_vehicle_data: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test coordinator recovers from expired vehicle access token."""
    await setup_platform(hass, normal_config_entry)
    assert normal_config_entry.state is ConfigEntryState.LOADED
    assert (state := hass.states.get("sensor.test_battery_level"))
    assert state.state != "unavailable"

    mock_vehicle_data.reset_mock()
    mock_vehicle_data.side_effect = OAuthExpired

    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert normal_config_entry.state is ConfigEntryState.LOADED
    assert (state := hass.states.get("sensor.test_battery_level"))
    assert state.state == "unavailable"
    assert normal_config_entry.data["token"]["expires_at"] == 0
    assert mock_vehicle_data.call_count == 1

    mock_vehicle_data.side_effect = None
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.test_battery_level"))
    assert state.state != "unavailable"
    assert mock_vehicle_data.call_count == 2