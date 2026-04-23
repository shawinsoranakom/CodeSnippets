async def test_color_light_with_temp(
    hass: HomeAssistant, mock_effect_conductor
) -> None:
    """Test a color light with temp."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.power_level = 65535
    bulb.color = [65535, 65535, 65535, 65535]
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
    assert attributes[ATTR_BRIGHTNESS] == 255
    assert attributes[ATTR_COLOR_MODE] == ColorMode.HS
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]
    assert attributes[ATTR_HS_COLOR] == (360.0, 100.0)
    assert attributes[ATTR_RGB_COLOR] == (255, 0, 0)
    assert attributes[ATTR_XY_COLOR] == (0.701, 0.299)

    bulb.color = [32000, None, 32000, 6000]

    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is True
    bulb.set_power.reset_mock()
    state = hass.states.get(entity_id)
    assert state.state == "on"
    attributes = state.attributes
    assert attributes[ATTR_BRIGHTNESS] == 125
    assert attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]
    assert attributes[ATTR_HS_COLOR] == (30.754, 7.122)
    assert attributes[ATTR_RGB_COLOR] == (255, 246, 237)
    assert attributes[ATTR_XY_COLOR] == (0.339, 0.338)
    bulb.color = [65535, 65535, 65535, 65535]

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
        "color": [65535, 65535, 25700, 65535],
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
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [1820, 19660, 65535, 3500],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": True,
        "set_saturation": True,
        "set_brightness": False,
        "set_kelvin": True,
    }
    bulb.set_waveform_optional.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (255, 30, 80)},
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [63107, 57824, 65535, 3500],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": True,
        "set_saturation": True,
        "set_brightness": False,
        "set_kelvin": True,
    }
    bulb.set_waveform_optional.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_XY_COLOR: (0.46, 0.376)},
        blocking=True,
    )
    assert bulb.set_waveform_optional.calls[-1][1]["rapid"] is False
    assert bulb.set_waveform_optional.calls[-1][1]["value"] == {
        "transient": False,
        "color": [4956, 30583, 65535, 3500],
        "period": 0,
        "cycles": 1,
        "skew_ratio": 0,
        "waveform": 0,
        "set_hue": True,
        "set_saturation": True,
        "set_brightness": False,
        "set_kelvin": True,
    }
    bulb.set_waveform_optional.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_colorloop"},
        blocking=True,
    )
    start_call = mock_effect_conductor.start.mock_calls
    first_call = start_call[0][1]
    assert isinstance(first_call[0], aiolifx_effects.EffectColorloop)
    assert first_call[1][0] == bulb
    mock_effect_conductor.start.reset_mock()
    mock_effect_conductor.stop.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_COLORLOOP,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS_PCT: 50, ATTR_SATURATION_MAX: 90},
        blocking=True,
    )
    start_call = mock_effect_conductor.start.mock_calls
    first_call = start_call[0][1]
    assert isinstance(first_call[0], aiolifx_effects.EffectColorloop)
    assert first_call[1][0] == bulb
    mock_effect_conductor.start.reset_mock()
    mock_effect_conductor.stop.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_COLORLOOP,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128, ATTR_SATURATION_MIN: 90},
        blocking=True,
    )
    start_call = mock_effect_conductor.start.mock_calls
    first_call = start_call[0][1]
    assert isinstance(first_call[0], aiolifx_effects.EffectColorloop)
    assert first_call[1][0] == bulb
    mock_effect_conductor.start.reset_mock()
    mock_effect_conductor.stop.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_pulse"},
        blocking=True,
    )
    assert len(mock_effect_conductor.stop.mock_calls) == 1
    start_call = mock_effect_conductor.start.mock_calls
    first_call = start_call[0][1]
    assert isinstance(first_call[0], aiolifx_effects.EffectPulse)
    assert first_call[1][0] == bulb
    mock_effect_conductor.start.reset_mock()
    mock_effect_conductor.stop.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_stop"},
        blocking=True,
    )
    assert len(mock_effect_conductor.stop.mock_calls) == 2