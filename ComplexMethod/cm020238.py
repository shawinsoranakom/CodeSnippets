async def test_paint_theme_service(hass: HomeAssistant) -> None:
    """Test the firmware flame and morph effects on a matrix device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
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

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PAINT_THEME,
        {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 4, ATTR_THEME: "autumn"},
        blocking=True,
    )

    bulb.power_level = 65535

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_color.calls) == 1
    call_dict = bulb.set_color.calls[0][1]
    call_dict.pop("callb")
    assert call_dict["value"] in [
        (5643, 65535, 32768, 3500),
        (15109, 65535, 32768, 3500),
        (8920, 65535, 32768, 3500),
        (10558, 65535, 32768, 3500),
    ]
    assert call_dict["duration"] == 4000
    bulb.set_color.reset_mock()
    bulb.set_power.reset_mock()

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PAINT_THEME,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_TRANSITION: 6,
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
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    assert len(bulb.set_power.calls) == 1
    assert len(bulb.set_color.calls) == 1
    call_dict = bulb.set_color.calls[0][1]
    call_dict.pop("callb")
    hue = round(call_dict["value"][0] / 65535 * 360)
    sat = round(call_dict["value"][1] / 65535 * 100)
    bri = call_dict["value"][2] >> 8
    kel = call_dict["value"][3]
    assert (hue, sat, bri, kel) in [
        (0, 100, 255, 3500),
        (60, 100, 255, 3500),
        (120, 100, 255, 3500),
        (180, 100, 255, 3500),
        (240, 100, 255, 3500),
        (300, 100, 255, 3500),
    ]
    assert call_dict["duration"] == 6000

    bulb.set_color.reset_mock()
    bulb.set_power.reset_mock()