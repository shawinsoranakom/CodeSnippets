async def test_light_invalid_hs_color(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test light that starts out with an invalid hs color."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: ["color_temp", "hs"],
            ATTR_COLOR_MODE: "hs",
            ATTR_HS_COLOR: 260,
        },
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_color_temp.value == 153
    assert acc.char_hue.value == 0
    assert acc.char_saturation.value == 75

    assert hasattr(acc, "char_color_temp")

    hass.states.async_set(entity_id, STATE_ON, {ATTR_COLOR_TEMP_KELVIN: 4464})
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert acc.char_color_temp.value == 224
    assert acc.char_hue.value == 27
    assert acc.char_saturation.value == 27

    hass.states.async_set(entity_id, STATE_ON, {ATTR_COLOR_TEMP_KELVIN: 2840})
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert acc.char_color_temp.value == 352
    assert acc.char_hue.value == 28
    assert acc.char_saturation.value == 61

    char_on_iid = acc.char_on.to_HAP()[HAP_REPR_IID]
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]
    char_hue_iid = acc.char_hue.to_HAP()[HAP_REPR_IID]
    char_saturation_iid = acc.char_saturation.to_HAP()[HAP_REPR_IID]
    char_color_temp_iid = acc.char_color_temp.to_HAP()[HAP_REPR_IID]

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {HAP_REPR_AID: acc.aid, HAP_REPR_IID: char_on_iid, HAP_REPR_VALUE: 1},
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 20,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 250,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_hue_iid,
                    HAP_REPR_VALUE: 50,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_saturation_iid,
                    HAP_REPR_VALUE: 50,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[0].data[ATTR_BRIGHTNESS_PCT] == 20
    assert call_turn_on[0].data[ATTR_COLOR_TEMP_KELVIN] == 4000

    assert len(events) == 1
    assert (
        events[-1].data[ATTR_VALUE]
        == f"Set state to 1, brightness at 20{PERCENTAGE}, color temperature at 250"
    )

    # Only set Hue
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_hue_iid,
                    HAP_REPR_VALUE: 30,
                }
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[1]
    assert call_turn_on[1].data[ATTR_HS_COLOR] == (30, 50)

    assert events[-1].data[ATTR_VALUE] == "set color at (30, 50)"

    # Only set Saturation
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_saturation_iid,
                    HAP_REPR_VALUE: 20,
                }
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[2]
    assert call_turn_on[2].data[ATTR_HS_COLOR] == (30, 20)

    assert events[-1].data[ATTR_VALUE] == "set color at (30, 20)"

    # Generate a conflict by setting hue and then color temp
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_hue_iid,
                    HAP_REPR_VALUE: 80,
                }
            ]
        },
        "mock_addr",
    )
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 320,
                }
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[3]
    assert call_turn_on[3].data[ATTR_COLOR_TEMP_KELVIN] == 3125
    assert events[-1].data[ATTR_VALUE] == "color temperature at 320"

    # Generate a conflict by setting color temp then saturation
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 404,
                }
            ]
        },
        "mock_addr",
    )
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_saturation_iid,
                    HAP_REPR_VALUE: 35,
                }
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[4]
    assert call_turn_on[4].data[ATTR_HS_COLOR] == (80, 35)
    assert events[-1].data[ATTR_VALUE] == "set color at (80, 35)"

    # Set from HASS
    hass.states.async_set(entity_id, STATE_ON, {ATTR_HS_COLOR: (100, 100)})
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert acc.char_color_temp.value == 404
    assert acc.char_hue.value == 100
    assert acc.char_saturation.value == 100