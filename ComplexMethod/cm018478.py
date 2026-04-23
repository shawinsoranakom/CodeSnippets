async def test_rpc_linkedgo_st802_thermostat(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: SnapshotAssertion,
) -> None:
    """Test LINKEDGO ST802 thermostat climate."""
    entity_id = "climate.test_name"

    device_fixture = await async_load_json_object_fixture(
        hass, "st802_gen3.json", DOMAIN
    )
    monkeypatch.setattr(mock_rpc_device, "shelly", device_fixture["shelly"])
    monkeypatch.setattr(mock_rpc_device, "status", device_fixture["status"])
    monkeypatch.setattr(mock_rpc_device, "config", device_fixture["config"])

    await init_integration(hass, 3, model=MODEL_LINKEDGO_ST802_THERMOSTAT)

    assert hass.states.get(entity_id) == snapshot(name=f"{entity_id}-state")

    assert entity_registry.async_get(entity_id) == snapshot(name=f"{entity_id}-entry")

    # Test HVAC mode cool
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["enum:201"], "value", "cool")
    mock_rpc_device.mock_update()

    mock_rpc_device.boolean_set.assert_called_once_with(201, True)
    mock_rpc_device.enum_set.assert_called_once_with(201, "cool")
    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.COOL

    # Test set temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 25},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 25)
    mock_rpc_device.mock_update()

    mock_rpc_device.number_set.assert_called_once_with(203, 25.0)
    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_TEMPERATURE) == 25

    # Test set humidity
    mock_rpc_device.number_set.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_ENTITY_ID: entity_id, ATTR_HUMIDITY: 66},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["number:202"], "value", 66)
    mock_rpc_device.mock_update()

    mock_rpc_device.number_set.assert_called_once_with(202, 66.0)
    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_HUMIDITY) == 66

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

    # Test set fan mode
    mock_rpc_device.enum_set.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_FAN_MODE: FAN_LOW},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["enum:200"], "value", "low")
    mock_rpc_device.mock_update()

    mock_rpc_device.enum_set.assert_called_once_with(200, "low")
    assert (state := hass.states.get(entity_id))
    assert state.attributes.get(ATTR_FAN_MODE) == FAN_LOW

    # Test HVAC mode off
    mock_rpc_device.boolean_set.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    monkeypatch.setitem(mock_rpc_device.status["boolean:201"], "value", False)
    mock_rpc_device.mock_update()

    mock_rpc_device.boolean_set.assert_called_once_with(201, False)
    assert (state := hass.states.get(entity_id))
    assert state.state == HVACMode.OFF

    # Test current temperature update
    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 25.1

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "number:201", "value", 22.4)
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 22.4