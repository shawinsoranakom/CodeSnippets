async def test_transitions_brightness_only(hass: HomeAssistant) -> None:
    """Test transitions with a brightness only device."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_brightness_bulb()
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
    assert attributes[ATTR_COLOR_MODE] == ColorMode.BRIGHTNESS
    assert attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.BRIGHTNESS,
    ]
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is False
    bulb.set_power.reset_mock()
    bulb.power_level = 0

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 5, ATTR_BRIGHTNESS: 100},
        blocking=True,
    )
    assert bulb.set_power.calls[0][0][0] is True
    call_dict = bulb.set_power.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {"duration": 5000}
    bulb.set_power.reset_mock()

    bulb.power_level = 0

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 5, ATTR_BRIGHTNESS: 200},
        blocking=True,
    )
    assert bulb.set_power.calls[0][0][0] is True
    call_dict = bulb.set_power.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {"duration": 5000}
    bulb.set_power.reset_mock()

    await hass.async_block_till_done()
    bulb.get_color.reset_mock()

    # Ensure we force an update after the transition
    with _patch_discovery(device=bulb):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
        await hass.async_block_till_done()
        assert len(bulb.get_color.calls) == 2