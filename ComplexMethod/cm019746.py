async def test_charge_energy_reset(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    mock_vehicle_data: AsyncMock,
) -> None:
    """Test reset detection for polling charge energy sensors."""

    freezer.move_to("2024-01-01 00:00:00+00:00")

    # Set initial charge_energy_added to 10
    initial_data = deepcopy(VEHICLE_DATA)
    initial_data["response"]["charge_state"]["charge_energy_added"] = 10.0
    mock_vehicle_data.return_value = initial_data
    await setup_platform(hass, normal_config_entry, [Platform.SENSOR])
    entity_id = "sensor.test_charge_energy_added"

    state = hass.states.get(entity_id)
    assert state.state == "10.0"
    assert state.attributes.get("last_reset") is None

    # Small correction should NOT trigger reset
    correction_data = deepcopy(VEHICLE_DATA)
    correction_data["response"]["charge_state"]["charge_energy_added"] = 9.5
    mock_vehicle_data.return_value = correction_data
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "9.5"
    assert state.attributes.get("last_reset") is None

    # Drop to 0 should trigger reset
    freezer.move_to("2024-01-01 01:00:00+00:00")
    reset_data = deepcopy(VEHICLE_DATA)
    reset_data["response"]["charge_state"]["charge_energy_added"] = 0
    mock_vehicle_data.return_value = reset_data
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "0"
    assert state.attributes.get("last_reset") is not None
    last_reset = state.attributes["last_reset"]

    # Additional 0 updates should not move last_reset forward
    freezer.move_to("2024-01-01 01:30:00+00:00")
    mock_vehicle_data.return_value = reset_data
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "0"
    assert state.attributes["last_reset"] == last_reset