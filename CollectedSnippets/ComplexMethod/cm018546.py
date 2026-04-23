async def test_rpc_device_virtual_switch(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
    name: str | None,
    entity_id: str,
) -> None:
    """Test a virtual switch for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    config["boolean:200"] = {
        "name": name,
        "meta": {"ui": {"view": "toggle"}},
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["boolean:200"] = {"value": True}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-boolean:200-boolean_generic"

    monkeypatch.setitem(mock_rpc_device.status["boolean:200"], "value", False)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    mock_rpc_device.boolean_set.assert_called_once_with(200, False)

    monkeypatch.setitem(mock_rpc_device.status["boolean:200"], "value", True)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    mock_rpc_device.boolean_set.assert_called_with(200, True)