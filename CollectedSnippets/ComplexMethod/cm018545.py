async def test_wall_display_relay_mode(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Wall Display in relay mode."""
    climate_entity_id = "climate.test_name"
    switch_entity_id = "switch.test_name_test_switch_0"
    monkeypatch.delitem(mock_rpc_device.status, "cover:0")

    config_entry = await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    assert (state := hass.states.get(climate_entity_id))
    assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 1

    new_status = deepcopy(mock_rpc_device.status)
    new_status["sys"]["relay_in_thermostat"] = False
    new_status.pop("thermostat:0")
    monkeypatch.setattr(mock_rpc_device, "status", new_status)

    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # the climate entity should be removed

    assert hass.states.get(climate_entity_id) is None
    assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 0

    # the switch entity should be created
    assert (state := hass.states.get(switch_entity_id))
    assert state.state == STATE_ON
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    assert (entry := entity_registry.async_get(switch_entity_id))
    assert entry.unique_id == "123456789ABC-switch:0"