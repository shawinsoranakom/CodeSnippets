async def test_smart_strip_effects(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test smart strip effects."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    features = [
        _mocked_feature("brightness", value=50),
        _mocked_feature("hsv", value=(10, 30, 5)),
        _mocked_feature(
            "color_temp", value=4000, minimum_value=4000, maximum_value=9000
        ),
    ]
    device = _mocked_device(
        modules=[Module.Light, Module.LightEffect], alias="my_light", features=features
    )
    light = device.modules[Module.Light]
    light_effect = device.modules[Module.LightEffect]

    with (
        _patch_discovery(device=device),
        _patch_single_discovery(device=device),
        _patch_connect(device=device),
    ):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "light.my_light"

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "Effect1"
    assert state.attributes[ATTR_EFFECT_LIST] == ["Off", "Effect1", "Effect2"]

    # Ensure setting color temp when an effect
    # is in progress calls set_effect to clear the effect
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 4000},
        blocking=True,
    )
    light_effect.set_effect.assert_called_once_with(LightEffect.LIGHT_EFFECTS_OFF)
    light.set_color_temp.assert_called_once_with(4000, brightness=None, transition=None)
    light_effect.set_effect.reset_mock()
    light.set_color_temp.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Effect2"},
        blocking=True,
    )
    light_effect.set_effect.assert_called_once_with(
        "Effect2", brightness=None, transition=None
    )
    light_effect.set_effect.reset_mock()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "Effect2"

    # Test setting light effect off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "off"},
        blocking=True,
    )
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "off"
    light.set_state.assert_not_called()

    # Test setting light effect to invalid value
    caplog.clear()
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Effect3"},
        blocking=True,
    )
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == "off"
    assert "Invalid effect Effect3 for" in caplog.text

    light_effect.effect = LightEffect.LIGHT_EFFECTS_OFF
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT] == EFFECT_OFF

    light.state = LightState(light_on=False)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=20))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_EFFECT] is None

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    light.set_state.assert_called_once()
    light.set_state.reset_mock()

    light.state = LightState(light_on=True)
    light_effect.effect_list = None
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_EFFECT_LIST] is None