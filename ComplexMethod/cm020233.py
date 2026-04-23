async def test_light_strip(hass: HomeAssistant) -> None:
    """Test a light strip."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_light_strip()
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
    assert len(bulb.set_color_zones.calls) == 0
    bulb.set_color_zones.reset_mock()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    assert len(bulb.set_color_zones.calls) == 0
    bulb.set_color_zones.reset_mock()

    bulb.color_zones = [
        (0, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
    ]

    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_HS_COLOR: (10, 30)},
        blocking=True,
    )
    # Single color uses the fast path
    assert bulb.set_waveform_optional.calls[-1][1]["value"]["color"] == [
        1820,
        19660,
        65535,
        3500,
    ]
    bulb.set_waveform_optional.reset_mock()
    assert len(bulb.set_color_zones.calls) == 0

    bulb.color_zones = [
        (0, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
    ]

    await hass.services.async_call(
        DOMAIN,
        "set_state",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (255, 10, 30)},
        blocking=True,
    )
    # Single color uses the fast path
    assert bulb.set_waveform_optional.calls[-1][1]["value"]["color"] == [
        64643,
        62964,
        65535,
        3500,
    ]
    bulb.set_waveform_optional.reset_mock()
    assert len(bulb.set_color_zones.calls) == 0

    bulb.color_zones = [
        (0, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
    ]

    await hass.services.async_call(
        DOMAIN,
        "set_state",
        {ATTR_ENTITY_ID: entity_id, ATTR_XY_COLOR: (0.3, 0.7)},
        blocking=True,
    )
    # Single color uses the fast path
    assert bulb.set_waveform_optional.calls[-1][1]["value"]["color"] == [
        15848,
        65535,
        65535,
        3500,
    ]
    bulb.set_waveform_optional.reset_mock()
    assert len(bulb.set_color_zones.calls) == 0

    bulb.color_zones = [
        (0, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (54612, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
        (46420, 65535, 65535, 3500),
    ]

    await hass.services.async_call(
        DOMAIN,
        "set_state",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )
    # multiple zones in effect and we are changing the brightness
    # we need to do each zone individually
    assert len(bulb.set_color.calls) == 0
    call_dict = bulb.set_color_zones.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 0,
        "color": [0, 65535, 32896, 3500],
        "duration": 0,
        "end_index": 0,
        "start_index": 0,
    }
    call_dict = bulb.set_color_zones.calls[1][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 0,
        "color": [54612, 65535, 32896, 3500],
        "duration": 0,
        "end_index": 1,
        "start_index": 1,
    }
    call_dict = bulb.set_color_zones.calls[7][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 1,
        "color": [46420, 65535, 32896, 3500],
        "duration": 0,
        "end_index": 7,
        "start_index": 7,
    }
    bulb.set_color_zones.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        "set_state",
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_RGB_COLOR: (255, 255, 255),
            ATTR_ZONES: [0, 2],
        },
        blocking=True,
    )
    # set a two zones
    assert len(bulb.set_color.calls) == 0
    call_dict = bulb.set_color_zones.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 0,
        "color": [0, 0, 65535, 3500],
        "duration": 0,
        "end_index": 0,
        "start_index": 0,
    }
    call_dict = bulb.set_color_zones.calls[1][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 1,
        "color": [0, 0, 65535, 3500],
        "duration": 0,
        "end_index": 2,
        "start_index": 2,
    }
    bulb.set_color_zones.reset_mock()

    bulb.get_color_zones.reset_mock()
    bulb.set_power.reset_mock()

    bulb.power_level = 0
    await hass.services.async_call(
        DOMAIN,
        "set_state",
        {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (255, 255, 255), ATTR_ZONES: [3]},
        blocking=True,
    )
    # set a one zone
    assert len(bulb.set_power.calls) == 2
    assert len(bulb.get_color_zones.calls) == 1
    assert len(bulb.set_color.calls) == 0
    call_dict = bulb.set_color_zones.calls[0][1]
    call_dict.pop("callb")
    assert call_dict == {
        "apply": 1,
        "color": [0, 0, 65535, 3500],
        "duration": 0,
        "end_index": 3,
        "start_index": 3,
    }
    bulb.get_color_zones.reset_mock()
    bulb.set_power.reset_mock()
    bulb.set_color_zones.reset_mock()

    bulb.set_color_zones = MockFailingLifxCommand(bulb)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "set_state",
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGB_COLOR: (255, 255, 255),
                ATTR_ZONES: [3],
            },
            blocking=True,
        )

    bulb.set_color_zones = MockLifxCommand(bulb)
    bulb.get_color_zones = MockFailingLifxCommand(bulb)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "set_state",
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGB_COLOR: (255, 255, 255),
                ATTR_ZONES: [3],
            },
            blocking=True,
        )

    bulb.get_color_zones = MockLifxCommand(
        bulb, msg_seq_num=0, msg_color=[0, 0, 65535, 3500] * 3, msg_index=0, msg_count=3
    )
    bulb.get_color = MockFailingLifxCommand(bulb)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "set_state",
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGB_COLOR: (255, 255, 255),
                ATTR_ZONES: [3],
            },
            blocking=True,
        )