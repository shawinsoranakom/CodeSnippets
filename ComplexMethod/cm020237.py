async def test_lightstrip_move_effect(hass: HomeAssistant) -> None:
    """Test the firmware move effect on a light strip."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_light_strip()
    bulb.product = 38
    bulb.power_level = 0
    bulb.color = [65535, 65535, 65535, 65535]
    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.my_bulb"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_move"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_multizone_effect.calls) == 1

    call_dict = bulb.set_multizone_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 1,
        "speed": 3.0,
        "direction": 0,
    }

    bulb.get_multizone_effect.reset_mock()
    bulb.set_multizone_effect.reset_mock()
    bulb.set_power.reset_mock()

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_MOVE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_SPEED: 4.5,
            ATTR_DIRECTION: "left",
            ATTR_THEME: "sports",
        },
        blocking=True,
    )

    bulb.power_level = 65535
    bulb.effect = {"name": "MOVE", "speed": 4.5, "direction": "Left"}
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_extended_color_zones.calls) == 1
    assert len(bulb.set_multizone_effect.calls) == 1
    call_dict = bulb.set_multizone_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 1,
        "speed": 4.5,
        "direction": 1,
    }
    bulb.get_multizone_effect.reset_mock()
    bulb.set_multizone_effect.reset_mock()
    bulb.set_power.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_stop"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(bulb.set_power.calls) == 0
    assert len(bulb.set_multizone_effect.calls) == 1
    call_dict = bulb.set_multizone_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 0,
        "speed": 3.0,
        "direction": 0,
    }
    bulb.get_multizone_effect.reset_mock()
    bulb.set_multizone_effect.reset_mock()
    bulb.set_power.reset_mock()