async def test_brightness_not_supported(hass: HomeAssistant) -> None:
    """Tests that a non-dimmable light should not support the brightness feature."""
    await setup_platform(
        hass,
        LIGHT_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
    )

    state = hass.states.get("light.name_1")
    assert state.state == "off"
    assert state.attributes[ATTR_COLOR_MODE] is None
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    with patch_bond_device_state(return_value={"light": 1}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    state = hass.states.get("light.name_1")
    assert state.state == "on"
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.ONOFF
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0