async def test_binary_sensor_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test binary sensor entities values and names."""
    with patch(
        "homeassistant.components.enphase_envoy.PLATFORMS", [Platform.BINARY_SENSOR]
    ):
        await setup_integration(hass, config_entry)

    sn = mock_envoy.data.enpower.serial_number
    entity_base = f"{Platform.BINARY_SENSOR}.enpower"

    assert (entity_state := hass.states.get(f"{entity_base}_{sn}_communicating"))
    assert entity_state.state == STATE_ON
    assert (entity_state := hass.states.get(f"{entity_base}_{sn}_grid_status"))
    assert entity_state.state == STATE_ON

    entity_base = f"{Platform.BINARY_SENSOR}.encharge"

    for sn in mock_envoy.data.encharge_inventory:
        assert (entity_state := hass.states.get(f"{entity_base}_{sn}_communicating"))
        assert entity_state.state == STATE_ON
        assert (entity_state := hass.states.get(f"{entity_base}_{sn}_dc_switch"))
        assert entity_state.state == STATE_ON