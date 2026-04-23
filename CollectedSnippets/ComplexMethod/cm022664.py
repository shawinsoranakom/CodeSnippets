async def test_light_brightness(
    hass: HomeAssistant, hk_driver, events: list[Event], supported_color_modes
) -> None:
    """Test light with brightness."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 255},
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # brightness to 100 when turning on a light on a freshly booted up server.
    assert acc.char_brightness.value != 0
    char_on_iid = acc.char_on.to_HAP()[HAP_REPR_IID]
    char_brightness_iid = acc.char_brightness.to_HAP()[HAP_REPR_IID]

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 100

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 102},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 40

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    call_turn_off = async_mock_service(hass, LIGHT_DOMAIN, "turn_off")

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {HAP_REPR_AID: acc.aid, HAP_REPR_IID: char_on_iid, HAP_REPR_VALUE: 1},
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 20,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[0].data[ATTR_BRIGHTNESS_PCT] == 20
    assert len(events) == 1
    assert (
        events[-1].data[ATTR_VALUE] == f"Set state to 1, brightness at 20{PERCENTAGE}"
    )

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {HAP_REPR_AID: acc.aid, HAP_REPR_IID: char_on_iid, HAP_REPR_VALUE: 1},
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 40,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on[1]
    assert call_turn_on[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[1].data[ATTR_BRIGHTNESS_PCT] == 40
    assert len(events) == 2
    assert (
        events[-1].data[ATTR_VALUE] == f"Set state to 1, brightness at 40{PERCENTAGE}"
    )

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {HAP_REPR_AID: acc.aid, HAP_REPR_IID: char_on_iid, HAP_REPR_VALUE: 1},
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] == f"Set state to 0, brightness at 0{PERCENTAGE}"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_brightness_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] == f"Set state to 0, brightness at 0{PERCENTAGE}"

    # 0 is a special case for homekit, see "Handle Brightness"
    # in update_state
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 0},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 1
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 255},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 100
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 0},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 1

    # Ensure floats are handled
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 55.66},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 22
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 108.4},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 43
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: supported_color_modes, ATTR_BRIGHTNESS: 0.0},
    )
    await hass.async_block_till_done()
    assert acc.char_brightness.value == 1