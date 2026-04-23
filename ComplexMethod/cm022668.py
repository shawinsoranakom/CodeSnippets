async def test_light_invalid_values(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test light with a variety of invalid values."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "hs",
            ATTR_HS_COLOR: (-1, -1),
        },
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_color_temp.value == 153
    assert acc.char_hue.value == 0
    assert acc.char_saturation.value == 0
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "color_temp",
            ATTR_COLOR_TEMP_KELVIN: -1,
        },
    )
    await hass.async_block_till_done()
    acc.run()

    assert acc.char_color_temp.value == 153
    assert acc.char_hue.value == 16
    assert acc.char_saturation.value == 100
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "color_temp",
            ATTR_COLOR_TEMP_KELVIN: sys.maxsize,
        },
    )
    await hass.async_block_till_done()

    assert acc.char_color_temp.value == 153
    assert acc.char_hue.value == 220
    assert acc.char_saturation.value == 41

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "color_temp",
            ATTR_COLOR_TEMP_KELVIN: 2000,
        },
    )
    await hass.async_block_till_done()

    assert acc.char_color_temp.value == 500
    assert acc.char_hue.value == 31
    assert acc.char_saturation.value == 95