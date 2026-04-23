async def test_rpc_device_rgb_profile(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device in RGB profile."""
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
    monkeypatch.delitem(mock_rpc_device.status, "rgbw:0")
    entity_id = "light.test_name_test_rgb_0"
    await init_integration(hass, 2)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_RGB_COLOR] == (45, 55, 65)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.RGB]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION

    # Turn on, RGB = [70, 80, 90]
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: [70, 80, 90]},
        blocking=True,
    )

    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgb:0", "rgb", [70, 80, 90])
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGB.Set", {"id": 0, "on": True, "rgb": [70, 80, 90]}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGB
    assert state.attributes[ATTR_RGB_COLOR] == (70, 80, 90)

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-rgb:0"