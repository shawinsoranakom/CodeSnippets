async def test_light_rgb_with_white_switch_to_temp(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
    supported_color_modes,
    state_props,
) -> None:
    """Test lights with RGBW/RGBWW that preserves brightness when switching to color temp."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, **state_props},
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_hue.value == 23
    assert acc.char_saturation.value == 100

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_hue.value == 23
    assert acc.char_saturation.value == 100
    assert acc.char_brightness.value == 100

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    char_hue_iid = acc.char_hue.to_HAP()[HAP_REPR_IID]
    char_saturation_iid = acc.char_saturation.to_HAP()[HAP_REPR_IID]
    char_color_temp_iid = acc.char_color_temp.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_hue_iid,
                    HAP_REPR_VALUE: 145,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_saturation_iid,
                    HAP_REPR_VALUE: 75,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[-1].data[ATTR_HS_COLOR] == (145, 75)
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "set color at (145, 75)"
    assert acc.char_brightness.value == 100
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 500,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[-1].data[ATTR_COLOR_TEMP_KELVIN] == 2000
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "color temperature at 500"
    assert acc.char_brightness.value == 100