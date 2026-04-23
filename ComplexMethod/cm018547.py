async def test_rpc_device_script_switch(
    hass: HomeAssistant,
    entity_registry: EntityRegistry,
    mock_rpc_device: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a script switch for RPC device."""
    config = deepcopy(mock_rpc_device.config)
    key = "script:1"
    script_name = "aioshelly_ble_integration"
    entity_id = f"switch.test_name_{script_name}"
    config[key] = {
        "id": 1,
        "name": script_name,
        "enable": False,
    }
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status[key] = {
        "running": True,
    }
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3)

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == f"123456789ABC-{key}-script"

    monkeypatch.setitem(mock_rpc_device.status[key], "running", False)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF
    mock_rpc_device.script_stop.assert_called_once_with(1)

    monkeypatch.setitem(mock_rpc_device.status[key], "running", True)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    mock_rpc_device.script_start.assert_called_once_with(1)