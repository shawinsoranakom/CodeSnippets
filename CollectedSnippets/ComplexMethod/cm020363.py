async def test_midnight_bounce_suppression(
    hass: HomeAssistant,
    mock_growatt_v1_api,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that stale yesterday values after midnight reset are suppressed.

    The Growatt API sometimes delivers stale yesterday values after a midnight
    reset (9.5 → 0 → 9.5 → 0), causing TOTAL_INCREASING double-counting.
    """
    with patch("homeassistant.components.growatt_server.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, mock_config_entry)

    entity_id = "sensor.test_plant_total_energy_today"

    # Initial state: 12.5 kWh produced today
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "12.5"

    # Step 1: Midnight reset — API returns 0 (legitimate reset)
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

    # Step 2: Stale bounce — API returns yesterday's value (12.5) after reset
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 12.5,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Bounce should be suppressed — state stays at 0
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "0"

    # Step 3: Another reset arrives — still 0 (no double-counting)
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

    # Step 4: Genuine new production — small value passes through
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