async def test_rpc_cct_light(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC CCT light."""
    entity_id = f"{LIGHT_DOMAIN}.test_name_cct_light_0"

    config = deepcopy(mock_rpc_device.config)
    config["cct:0"] = {"id": 0, "name": None, "ct_range": [3333, 5555]}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["cct:0"] = {"id": 0, "output": False, "brightness": 77, "ct": 3666}
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 2)

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-cct:0"

    # Turn off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.call_rpc.assert_called_once_with("CCT.Set", {"id": 0, "on": False})

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Turn on
    mock_rpc_device.call_rpc.reset_mock()
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cct:0", "output", True)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.mock_update()
    mock_rpc_device.call_rpc.assert_called_once_with("CCT.Set", {"id": 0, "on": True})

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP
    assert state.attributes[ATTR_BRIGHTNESS] == 196  # 77% of 255
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 3666
    assert state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 3333
    assert state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 5555

    # Turn on, brightness = 88
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS_PCT: 88},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cct:0", "brightness", 88)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "CCT.Set", {"id": 0, "on": True, "brightness": 88}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 224  # 88% of 255

    # Turn on, color temp = 4444 K
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 4444},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "cct:0", "ct", 4444)

    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "CCT.Set", {"id": 0, "on": True, "ct": 4444}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 4444