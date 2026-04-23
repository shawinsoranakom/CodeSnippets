async def test_midnight_bounce_repeated(
    hass: HomeAssistant,
    mock_growatt_v1_api,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test multiple consecutive stale bounces are all suppressed."""
    with patch("homeassistant.components.growatt_server.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, mock_config_entry)

    entity_id = "sensor.test_plant_total_energy_today"

    # Set up a known pre-reset value
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 8.0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "8.0"

    # Midnight reset
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0"

    # First stale bounce — suppressed
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 8.0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0"

    # Back to 0
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0"

    # Second stale bounce — also suppressed
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 8.0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0"

    # Back to 0 again
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0,
        "total_energy": 1250.0,
        "current_power": 0,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0"

    # Finally, genuine new production passes through
    mock_growatt_v1_api.plant_energy_overview.return_value = {
        "today_energy": 0.2,
        "total_energy": 1250.2,
        "current_power": 1000,
    }
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(entity_id).state == "0.2"