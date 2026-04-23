async def test_light_rgbww_with_color_temp_conversion(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
) -> None:
    """Test lights with RGBWW convert color temp as expected."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBWW],
            ATTR_RGBWW_COLOR: (128, 50, 0, 255, 255),
            ATTR_RGB_COLOR: (128, 50, 0),
            ATTR_HS_COLOR: (23.438, 100.0),
            ATTR_BRIGHTNESS: 255,
            ATTR_COLOR_MODE: ColorMode.RGBWW,
        },
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
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]

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
                    HAP_REPR_VALUE: 200,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[-1].data[ATTR_RGBWW_COLOR] == (0, 0, 0, 220, 35)
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "color temperature at 200"
    assert acc.char_brightness.value == 100

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGBWW],
            ATTR_RGBWW_COLOR: (0, 0, 0, 128, 255),
            ATTR_RGB_COLOR: (255, 163, 79),
            ATTR_HS_COLOR: (28.636, 69.02),
            ATTR_BRIGHTNESS: 180,
            ATTR_COLOR_MODE: ColorMode.RGBWW,
        },
    )
    await hass.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 100,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[-1].data[ATTR_BRIGHTNESS_PCT] == 100
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] == "brightness at 100%"
    assert acc.char_brightness.value == 100