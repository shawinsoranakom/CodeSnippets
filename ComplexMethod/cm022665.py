async def test_light_color_temperature(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test light with color temperature."""
    entity_id = "light.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_COLOR_MODES: ["color_temp"], ATTR_COLOR_TEMP_KELVIN: 5263},
    )
    await hass.async_block_till_done()
    acc = Light(hass, hk_driver, "Light", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_color_temp.value == 190

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_color_temp.value == 190

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    char_color_temp_iid = acc.char_color_temp.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_color_temp_iid,
                    HAP_REPR_VALUE: 250,
                }
            ]
        },
        "mock_addr",
    )
    await _wait_for_light_coalesce(hass)
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[0].data[ATTR_COLOR_TEMP_KELVIN] == 4000
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "color temperature at 250"