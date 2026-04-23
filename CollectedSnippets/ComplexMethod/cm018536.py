async def test_rpc_device_rgbw_profile(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test RPC device in RGBW profile."""
    for i in range(SHELLY_PLUS_RGBW_CHANNELS):
        monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
    monkeypatch.delitem(mock_rpc_device.status, "rgb:0")
    entity_id = "light.test_name_test_rgbw_0"
    await init_integration(hass, 2)

    # Test initial
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_RGBW_COLOR] == (21, 22, 23, 120)
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.RGBW]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == LightEntityFeature.TRANSITION

    # Turn on, RGBW = [72, 82, 92, 128]
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: [72, 82, 92, 128]},
        blocking=True,
    )

    mutate_rpc_device_status(
        monkeypatch, mock_rpc_device, "rgbw:0", "rgb", [72, 82, 92]
    )
    mutate_rpc_device_status(monkeypatch, mock_rpc_device, "rgbw:0", "white", 128)
    mock_rpc_device.mock_update()

    mock_rpc_device.call_rpc.assert_called_once_with(
        "RGBW.Set", {"id": 0, "on": True, "rgb": [72, 82, 92], "white": 128}
    )

    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.RGBW
    assert state.attributes[ATTR_RGBW_COLOR] == (72, 82, 92, 128)

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-rgbw:0"