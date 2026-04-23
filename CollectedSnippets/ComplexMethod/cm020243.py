async def test_transitions_color_bulb(hass: HomeAssistant) -> None:
    """Test transitions with a color bulb."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_bulb_new_firmware()
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
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is False
    bulb.set_power.reset_mock()
    bulb.power_level = 0

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_off",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_TRANSITION: 5,
        },
        blocking=True,
    )
    assert bulb.set_power.calls[0][0][0] is False
    call_dict = bulb.set_power.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {"duration": 0}  # already off
    bulb.set_power.reset_mock()
    bulb.set_color.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_RGB_COLOR: (255, 5, 10),
            ATTR_ENTITY_ID: entity_id,
            ATTR_TRANSITION: 5,
            ATTR_BRIGHTNESS: 100,
        },
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [65316, 64249, 25700, 3500],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": True,
        "set_saturation": True,
        "set_brightness": True,
        "set_kelvin": True,
    }
    assert bulb.set_power.calls[0][0][0] is True
    call_dict = bulb.set_power.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {"duration": 5000}
    bulb.set_power.reset_mock()
    bulb.set_waveform_optional.reset_mock()

    bulb.power_level = 12800

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {
            ATTR_RGB_COLOR: (5, 5, 10),
            ATTR_ENTITY_ID: entity_id,
            ATTR_TRANSITION: 5,
            ATTR_BRIGHTNESS: 200,
        },
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [43690, 32767, 51400, 3500],
        "period": 5000,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": True,
        "set_saturation": True,
        "set_brightness": True,
        "set_kelvin": True,
    }
    bulb.set_power.reset_mock()
    bulb.set_waveform_optional.reset_mock()

    await hass.async_block_till_done()
    bulb.get_color.reset_mock()

    # Ensure we force an update after the transition
    with _patch_discovery(device=bulb):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
        await hass.async_block_till_done()
        assert len(bulb.get_color.calls) == 2

    bulb.set_power.reset_mock()
    bulb.set_waveform_optional.reset_mock()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_off",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_TRANSITION: 5,
        },
        blocking=True,
    )
    assert bulb.set_power.calls[0][0][0] is False
    call_dict = bulb.set_power.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {"duration": 5000}
    bulb.set_power.reset_mock()
    bulb.set_waveform_optional.reset_mock()