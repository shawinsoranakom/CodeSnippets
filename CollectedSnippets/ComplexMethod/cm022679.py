async def test_light_set_brightness_and_color_temp(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test light with all chars in one go."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.COLOR_TEMP],
            ATTR_BRIGHTNESS: 255,
        },
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # brightness to 100 when turning on a light on a freshly booted up server.
    assert acc.char_brightness.value != 0
    char_on_iid = acc.char_on.to_HAP()[HAP_REPR_IID]
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]
    char_color_temp_iid = acc.char_color_temp.to_HAP()[HAP_REPR_IID]

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 100

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: [ColorMode.COLOR_TEMP], ATTR_BRIGHTNESS: 102},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 40

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.COLOR_TEMP],
            ATTR_COLOR_TEMP_KELVIN: (4461),
        },
    )
    await hass.async_block_till_done()
    assert acc.char_color_temp.value == 224

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