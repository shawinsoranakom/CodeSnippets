async def test_rpc_device_virtual_number_sensor(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
    original_unit: str,
    expected_unit: str | None,
) -> None:
    """Test a virtual number sensor for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["number:203"] = {
        "name": name,
        "min": 0,
        "max": 100,
        "meta": {"ui": {"step": 0.1, "unit": original_unit, "view": "label"}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["number:203"] = {"value": 34.5}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == "34.5"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == expected_unit

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-number:203-number_generic"

    monkeypatch.setitem(mock_rpc_device.status["number:203"], "value", 56.7)
    mock_rpc_device.mock_update()
    assert (state := hass.states.get(entity_id))
    assert state.state == "56.7"