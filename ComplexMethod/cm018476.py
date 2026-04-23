async def test_wall_display_thermostat_mode_external_actuator(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Wall Display in thermostat mode with an external actuator."""
    climate_entity_id = "climate.test_name"
    switch_entity_id = "switch.test_name_test_switch_0"

    new_status = deepcopy(mock_rpc_device.status)
    new_status["sys"]["relay_in_thermostat"] = False
    new_status.pop("cover:0")
    monkeypatch.setattr(mock_rpc_device, "status", new_status)

    await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    # the switch entity should be created
    assert (state := hass.states.get(switch_entity_id))
    assert state.state == STATE_ON
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    # the climate entity should be created
    assert (state := hass.states.get(climate_entity_id))
    assert state.state == HVACMode.HEAT
    assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 1

    assert (entry := entity_registry.async_get(climate_entity_id))
    assert entry.unique_id == "123456789ABC-thermostat:0"