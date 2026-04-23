async def test_light_rgbwx_with_color_temp_and_brightness(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
    supported_color_modes,
    state_props,
    turn_on_props_with_brightness,
) -> None:
    """Test lights with RGBW/RGBWW with color temp support and setting brightness."""
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

    char_color_temp_iid = acc.char_color_temp.to_HAP()[HAP_REPR_IID]
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 200,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 75,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    for k, v in turn_on_props_with_brightness.items():
        assert call_turn_on[-1].data[k] == v
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "brightness at 75%, color temperature at 200"
    assert acc.char_brightness.value == 75