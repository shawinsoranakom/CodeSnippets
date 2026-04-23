async def test_rpc_light(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC light."""
    entity_id = f"{LIGHT_DOMAIN}.test_light_0"
    monkeypatch.delitem(mock_rpc_device.status, "switch:0")
    await init_integration(hass, 2)

    # Turn on
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.call_rpc.assert_called_once_with("Light.Set", {"id": 0, "on": True})

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 135

    # Turn off
    mock_rpc_device.call_rpc.reset_mock()
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "light:0", "output", False)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.mock_update()
    mock_rpc_device.call_rpc.assert_called_once_with(
        "Light.Set", {"id": 0, "on": False}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Turn on, brightness = 33
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 33},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "light:0", "output", True)
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "light:0", "brightness", 13)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "Light.Set", {"id": 0, "on": True, "brightness": 13}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 33

    # Turn on, transition = 10.1
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 10.1},
        blocking=True,
    )

    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "Light.Set", {"id": 0, "on": True, "transition_duration": 10.1}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON

    # Turn off, transition = 0.4, should be limited to 0.5
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 0.4},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "light:0", "output", False)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "Light.Set", {"id": 0, "on": False, "transition_duration": 0.5}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-light:0"