async def test_rpc_climate_hvac_mode(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: SnapshotAssertion,
) -> None:
    """Test climate hvac mode service."""
    entity_id = "climate.test_name"

    await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    assert (state := hass.states.get(entity_id)) == snapshot(name=f"{entity_id}-state")

    assert entity_registry.async_get(entity_id) == snapshot(name=f"{entity_id}-entry")

    monkeypatch.setitem(mock_rpc_device.status["thermostat:0"], "output", False)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 44.4

    monkeypatch.setitem(mock_rpc_device.status["thermostat:0"], "enable", False)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    mock_rpc_device.climate_set_hvac_mode.assert_called_once_with(0, str(HVACMode.OFF))
    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF