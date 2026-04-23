async def test_rpc_climate_without_humidity(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test climate entity without the humidity value."""
    entity_id = "climate.test_name"
    new_status = deepcopy(mock_rpc_device.status)
    new_status.pop("humidity:0")
    monkeypatch.setattr(mock_rpc_device, "status", new_status)

    await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 23
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 12.3
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    assert ATTR_CURRENT_HUMIDITY not in state.attributes

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-thermostat:0"