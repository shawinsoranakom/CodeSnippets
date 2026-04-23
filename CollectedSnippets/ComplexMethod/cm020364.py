async def test_normal_reset_no_bounce(
    hass: HomeAssistant,
    mock_growatt_v1_api,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that normal midnight reset without bounce passes through correctly."""
    with patch("homeassistant.components.growatt_server.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, mock_config_entry)

    entity_id = "sensor.test_plant_total_energy_today"

    # Initial state: 9.5 kWh
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 9.5,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "9.5"

    # Midnight reset — API returns 0
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "0"

    # No bounce — genuine new production starts
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0.1,
        "total_energy": 1250.1,
        "current_power": 500,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "0.1"

    # Production continues normally
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 1.5,
        "total_energy": 1251.5,
        "current_power": 2000,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "1.5"