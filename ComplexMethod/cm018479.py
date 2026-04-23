async def test_rpc_linkedgo_st1820_thermostat(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: SnapshotAssertion,
) -> None:
    """Test LINKEDGO ST1820 thermostat climate."""
    entity_id = "climate.test_name"

    device_fixture = await async_load_json_object_fixture(
        hass, "st1820_gen3.json", DOMAIN
    )
    monkeypatch.setattr(mock_rpc_device, "shelly", device_fixture["shelly"])
    monkeypatch.setattr(mock_rpc_device, "status", device_fixture["status"])
    monkeypatch.setattr(mock_rpc_device, "config", device_fixture["config"])

    await init_integration(hass, 3, model=MODEL_LINKEDGO_ST1820_THERMOSTAT)

    assert hass.states.get(entity_id) == snapshot(name=f"{entity_id}-state")

    assert entity_registry.async_get(entity_id) == snapshot(name=f"{entity_id}-entry")

    # Test set temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 25},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["number:202"], "value", 25)
    mock_rpc_device.mock_update()

    mock_rpc_device.number_set.assert_called_once_with(202, 25.0)
    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_TEMPERATURE) == 25

    # Anti-Freeze preset mode
    mock_rpc_device.boolean_set.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: PRESET_FROST_PROTECTION},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["boolean:200"], "value", True)
    mock_rpc_device.mock_update()

    mock_rpc_device.boolean_set.assert_called_once_with(200, True)
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_FROST_PROTECTION

    # Test HVAC mode off
    mock_rpc_device.boolean_set.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["boolean:202"], "value", False)
    mock_rpc_device.mock_update()

    mock_rpc_device.boolean_set.assert_called_once_with(202, False)
    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF