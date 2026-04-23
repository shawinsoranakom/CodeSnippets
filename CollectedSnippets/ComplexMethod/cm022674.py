async def test_light_rgb_or_w_lights(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
) -> None:
    """Test lights with RGB or W lights."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGB, ColorMode.WHITE],
            ATTR_RGBW_COLOR: (128, 50, 0, 255),
            ATTR_RGB_COLOR: (128, 50, 0),
            ATTR_HS_COLOR: (23.438, 100.0),
            ATTR_BRIGHTNESS: 255,
            ATTR_COLOR_MODE: ColorMode.RGB,
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
    assert acc.char_color_temp.value == 153

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    char_hue_iid = acc.char_hue.to_HAP()[HAP_REPR_IID]
    char_saturation_iid = acc.char_saturation.to_HAP()[HAP_REPR_IID]
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]
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
                    HAP_REPR_VALUE: acc.min_mireds,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 25,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[-1].data[ATTR_WHITE] == round(25 * 255 / 100)
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "brightness at 25%, color temperature at 153"
    assert acc.char_brightness.value == 25

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.RGB, ColorMode.WHITE],
            ATTR_BRIGHTNESS: 255,
            ATTR_COLOR_MODE: ColorMode.WHITE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_hue.value == 0
    assert acc.char_saturation.value == 0
    assert acc.char_brightness.value == 100
    assert acc.char_color_temp.value == 153