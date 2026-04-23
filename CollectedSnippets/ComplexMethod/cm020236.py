async def test_sky_effect(hass: HomeAssistant) -> None:
    """Test the firmware sky effect on a ceiling device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_ceiling()
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

    # SKY effect test
    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_SKY,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PALETTE: None,
            ATTR_SKY_TYPE: "Clouds",
            ATTR_CLOUD_SATURATION_MAX: 180,
            ATTR_CLOUD_SATURATION_MIN: 50,
        },
        blocking=True,
    )

    bulb.power_level = 65535
    bulb.effect = {
        "effect": "SKY",
        "palette": None,
        "sky_type": 2,
        "cloud_saturation_min": 50,
        "cloud_saturation_max": 180,
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
        "effect": 5,
        "speed": 50,
        "palette": [],
        "sky_type": 2,
        "cloud_saturation_min": 50,
        "cloud_saturation_max": 180,
    }
    bulb.get_tile_effect.reset_mock()
    bulb.set_tile_effect.reset_mock()
    bulb.set_power.reset_mock()

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EFFECT_SKY,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PALETTE: [
                (200, 100, 1, 3500),
                (241, 100, 1, 3500),
                (189, 100, 8, 3500),
                (40, 100, 100, 3500),
                (40, 50, 100, 3500),
                (0, 0, 100, 6500),
            ],
            ATTR_SKY_TYPE: "Sunrise",
            ATTR_CLOUD_SATURATION_MAX: 180,
            ATTR_CLOUD_SATURATION_MIN: 50,
        },
        blocking=True,
    )

    bulb.power_level = 65535
    bulb.effect = {
        "effect": "SKY",
        "palette": [
            (200, 100, 1, 3500),
            (241, 100, 1, 3500),
            (189, 100, 8, 3500),
            (40, 100, 100, 3500),
            (40, 50, 100, 3500),
            (0, 0, 100, 6500),
        ],
        "sky_type": 0,
        "cloud_saturation_min": 50,
        "cloud_saturation_max": 180,
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
        "effect": 5,
        "speed": 50,
        "palette": [
            (36408, 65535, 65535, 3500),
            (43872, 65535, 65535, 3500),
            (34406, 65535, 5243, 3500),
            (7281, 65535, 65535, 3500),
            (7281, 32768, 65535, 3500),
            (0, 0, 65535, 6500),
        ],
        "sky_type": 0,
        "cloud_saturation_min": 50,
        "cloud_saturation_max": 180,
    }
    bulb.get_tile_effect.reset_mock()
    bulb.set_tile_effect.reset_mock()
    bulb.set_power.reset_mock()