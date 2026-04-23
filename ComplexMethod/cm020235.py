async def test_matrix_flame_morph_effects(hass: HomeAssistant) -> None:
    """Test the firmware flame and morph effects on a matrix device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_tile()
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

    # FLAME effect test
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "effect_flame"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_tile_effect.calls) == 1

    call_dict = bulb.set_tile_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 3,
        "speed": 3,
        "palette": [],
        "sky_type": None,
        "cloud_saturation_min": None,
        "cloud_saturation_max": None,
    }
    bulb.get_tile_effect.reset_mock()
    bulb.set_tile_effect.reset_mock()
    bulb.set_power.reset_mock()

    # MORPH effect tests
    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_MORPH,
        {ATTR_ENTITY_ID: entity_id, ATTR_SPEED: 4, ATTR_THEME: "autumn"},
        blocking=True,
    )

    bulb.power_level = 65535
    bulb.effect = {
        "effect": "MORPH",
        "speed": 4.0,
        "palette": [
            (5643, 65535, 32768, 3500),
            (15109, 65535, 32768, 3500),
            (8920, 65535, 32768, 3500),
            (10558, 65535, 32768, 3500),
        ],
    }
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_tile_effect.calls) == 1
    call_dict = bulb.set_tile_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 2,
        "speed": 4,
        "palette": [
            (5643, 65535, 32768, 3500),
            (15109, 65535, 32768, 3500),
            (8920, 65535, 32768, 3500),
            (10558, 65535, 32768, 3500),
        ],
        "sky_type": None,
        "cloud_saturation_min": None,
        "cloud_saturation_max": None,
    }
    bulb.get_tile_effect.reset_mock()
    bulb.set_tile_effect.reset_mock()
    bulb.set_power.reset_mock()

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_MORPH,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_SPEED: 6,
            ATTR_PALETTE: [
                (0, 100, 255, 3500),
                (60, 100, 255, 3500),
                (120, 100, 255, 3500),
                (180, 100, 255, 3500),
                (240, 100, 255, 3500),
                (300, 100, 255, 3500),
            ],
        },
        blocking=True,
    )

    bulb.power_level = 65535
    bulb.effect = {
        "effect": "MORPH",
        "speed": 6,
        "palette": [
            (0, 65535, 65535, 3500),
            (10922, 65535, 65535, 3500),
            (21845, 65535, 65535, 3500),
            (32768, 65535, 65535, 3500),
            (43690, 65535, 65535, 3500),
            (54612, 65535, 65535, 3500),
        ],
    }
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_tile_effect.calls) == 1
    call_dict = bulb.set_tile_effect.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "effect": 2,
        "speed": 6,
        "palette": [
            (0, 65535, 65535, 3500),
            (10922, 65535, 65535, 3500),
            (21845, 65535, 65535, 3500),
            (32768, 65535, 65535, 3500),
            (43690, 65535, 65535, 3500),
            (54613, 65535, 65535, 3500),
        ],
        "sky_type": None,
        "cloud_saturation_min": None,
        "cloud_saturation_max": None,
    }
    bulb.get_tile_effect.reset_mock()
    bulb.set_tile_effect.reset_mock()
    bulb.set_power.reset_mock()