async def test_rpc_rgbcct_light(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC RGBCCT light."""
    entity_id = f"{LIGHT_DOMAIN}.test_name"

    config = deepcopy(mock_rpc_device.config)
    config["rgbcct:0"] = {"id": 0, "name": None}
    monkeypatch.setattr(mock_rpc_device, "config", config)

    status = deepcopy(mock_rpc_device.status)
    status["rgbcct:0"] = {
        "id": 0,
        "output": False,
        "brightness": 44,
        "ct": 3349,
        "rgb": [76, 140, 255],
        "mode": "cct",
    }
    monkeypatch.setattr(mock_rpc_device, "status", status)

    await init_integration(hass, 3, MODEL_MULTICOLOR_BULB_G3)

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-rgbcct:0"

    # Turn off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBCCT.Set", {"id": 0, "on": False}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_OFF

    # Turn on
    mock_rpc_device.call_rpc.reset_mock()
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgbcct:0", "output", True)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBCCT.Set", {"id": 0, "on": True}
    )
    mock_rpc_device.mock_update()

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP
    assert state.attributes[ATTR_BRIGHTNESS] == 112
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 3349
    assert state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN] == 2700
    assert state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN] == 6500

    # Turn on, brightness = 88
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS_PCT: 88},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgbcct:0", "brightness", 88)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBCCT.Set", {"id": 0, "on": True, "brightness": 88}
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

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgbcct:0", "ct", 4444)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBCCT.Set", {"id": 0, "on": True, "ct": 4444, "mode": "cct"}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_TEMP_KELVIN] == 4444

    # Turn on, color 100, 150, 200
    mock_rpc_device.call_rpc.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: [100, 150, 200]},
        blocking=True,
    )

    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "rgbcct:0", "rgb", [100, 150, 200]
    )
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgbcct:0", "mode", "rgb")
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBCCT.Set", {"id": 0, "on": True, "rgb": [100, 150, 200], "mode": "rgb"}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGB
    assert state.attributes[ATTR_RGB_COLOR] == (100, 150, 200)