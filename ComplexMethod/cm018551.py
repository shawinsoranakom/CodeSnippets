async def test_rpc_device_virtual_number(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
    original_unit: str,
    expected_unit: str | None,
    view: str,
    mode: NumberMode,
) -> None:
    """Test a virtual number for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["number:203"] = {
        "name": name,
        "min": 0,
        "max": 100,
        "meta": {"ui": {"step": 0.1, "unit": original_unit, "view": view}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["number:203"] = {"value": 12.3}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == "12.3"
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 0.1
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == expected_unit
    assert state.attributes.get(ATTR_MODE) is mode

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-number:203-number_generic"

    monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 78.9)
    mock_rpc_device.mock_update()
    assert (state := hass.states.get(entity_id))
    assert state.state == "78.9"

    monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 56.7)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 56.7},
        blocking=True,
    )
    mock_rpc_device.mock_update()
    mock_rpc_device.number_set.assert_called_once_with(203, 56.7)

    assert (state := hass.states.get(entity_id))
    assert state.state == "56.7"