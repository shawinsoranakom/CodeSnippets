async def test_white_bulb(hass: HomeAssistant) -> None:
    """Test a white bulb."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_white_bulb()
    bulb.power_level = 65535
    bulb.color = [32000, None, 32000, 6000]
    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.my_bulb"

    state = hass.states.get(entity_id)
    assert state.state == "on"
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 125
    assert attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
    ]
    assert attributes[ATTR_COLOR_TEMP_KELVIN] == 6000
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is False
    bulb.set_power.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is True
    bulb.set_power.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [32000, None, 25700, 6000],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": False,
        "set_saturation": False,
        "set_brightness": True,
        "set_kelvin": False,
    }
    bulb.set_waveform_optional.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 2500},
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [32000, 0, 32000, 2500],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": False,
        "set_saturation": True,
        "set_brightness": False,
        "set_kelvin": True,
    }
    bulb.set_waveform_optional.reset_mock()