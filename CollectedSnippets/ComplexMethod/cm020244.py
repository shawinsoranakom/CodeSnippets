async def test_light_strip_zones_not_populated_yet(hass: HomeAssistant) -> None:
    """Test a light strip were zones are not populated initially."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_light_strip()
    bulb.power_level = 65535
    bulb.color_zones = None
    bulb.color = [65535, 65535, 65535, 65535]
    bulb.get_color_zones = next(
        iter(
            [
                MockLifxCommand(
                    bulb,
                    msg_seq_num=0,
                    msg_color=[0, 0, 65535, 3500] * 8,
                    msg_index=0,
                    msg_count=16,
                ),
                MockLifxCommand(
                    bulb,
                    msg_seq_num=1,
                    msg_color=[0, 0, 65535, 3500] * 8,
                    msg_index=0,
                    msg_count=16,
                ),
                MockLifxCommand(
                    bulb,
                    msg_seq_num=2,
                    msg_color=[0, 0, 65535, 3500] * 8,
                    msg_index=8,
                    msg_count=16,
                ),
            ]
        )
    )
    assert bulb.get_color_zones.calls == []

    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "light.my_bulb"
    # Make sure we at least try to fetch the first zone
    # to ensure we populate the zones from the 503 response
    assert len(bulb.get_color_zones.calls) == 3
    # Once to populate the number of zones
    assert bulb.get_color_zones.calls[0][1]["start_index"] == 0
    # Again once we know the number of zones
    assert bulb.get_color_zones.calls[1][1]["start_index"] == 0
    assert bulb.get_color_zones.calls[2][1]["start_index"] == 8

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

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert bulb.set_power.calls[0][0][0] is True
    bulb.set_power.reset_mock()

    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON