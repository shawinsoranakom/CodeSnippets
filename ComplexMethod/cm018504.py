async def test_rpc_device_virtual_enum_sensor(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
    value: str | None,
    expected_state: str,
) -> None:
    """Test a virtual enum sensor for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["enum:203"] = {
        "name": name,
        "options": ["one", "two", "three"],
        "meta": {"ui": {"view": "label", "titles": {"one": "Title 1", "two": None}}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["enum:203"] = {"value": value}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == expected_state
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.ENUM
    assert state.attributes.get(ATTR_OPTIONS) == ["Title 1", "two", "three"]

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-enum:203-enum_generic"

    monkeypatch.setitem(mock_rpc_device.status["enum:203"], "value", "two")
    mock_rpc_device.mock_update()
    assert (state := hass.states.get(entity_id))
    assert state.state == "two"