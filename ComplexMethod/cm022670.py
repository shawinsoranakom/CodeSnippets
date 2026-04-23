async def test_reversed_color_temp_min_max(hass: HomeAssistant, hk_driver) -> None:
    """Test light with a reversed color temp min max."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "hs",
            ATTR_COLOR_TEMP_KELVIN: 2000,
            ATTR_MAX_COLOR_TEMP_KELVIN: 3000,
            ATTR_MIN_COLOR_TEMP_KELVIN: 4000,
            ATTR_HS_COLOR: (-1, -1),
        },
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_color_temp.value == 333
    assert acc.char_color_temp.properties[PROP_MAX_VALUE] == 333
    assert acc.char_color_temp.properties[PROP_MIN_VALUE] == 250
    assert acc.char_hue.value == 31
    assert acc.char_saturation.value == 95
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "color_temp",
            ATTR_MAX_COLOR_TEMP_KELVIN: 4000,
            ATTR_MIN_COLOR_TEMP_KELVIN: 3000,
            ATTR_COLOR_TEMP_KELVIN: -1,
        },
    )
    await hass.async_block_till_done()
    acc.run()

    assert acc.char_color_temp.value == 250
    assert acc.char_hue.value == 16
    assert acc.char_saturation.value == 100
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "color_temp",
            ATTR_MAX_COLOR_TEMP_KELVIN: 4000,
            ATTR_MIN_COLOR_TEMP_KELVIN: 3000,
            ATTR_COLOR_TEMP_KELVIN: sys.maxsize,
        },
    )
    await hass.async_block_till_done()

    assert acc.char_color_temp.value == 250
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

    assert acc.char_color_temp.value == 250
    assert acc.char_hue.value == 220
    assert acc.char_saturation.value == 41