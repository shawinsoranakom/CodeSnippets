async def test_input_select_switch(
    hass: HomeAssistant, hk_driver, events: list[Event], domain
) -> None:
    """Test if select switch accessory is handled correctly."""
    entity_id = f"{domain}.test"

    hass.states.async_set(
        entity_id, "option1", {ATTR_OPTIONS: ["option1", "option2", "option3"]}
    )
    await hass.async_block_till_done()
    acc = SelectSwitch(hass, hk_driver, "SelectSwitch", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    switch_service = acc.get_service(SERV_OUTLET)
    configured_name_char = switch_service.get_characteristic(CHAR_CONFIGURED_NAME)
    assert configured_name_char.value == "option1"

    assert acc.select_chars["option1"].value is True
    assert acc.select_chars["option2"].value is False
    assert acc.select_chars["option3"].value is False

    call_select_option = async_mock_service(hass, domain, SERVICE_SELECT_OPTION)
    acc.select_chars["option2"].client_update_value(True)
    await hass.async_block_till_done()

    assert call_select_option
    assert call_select_option[0].data == {"entity_id": entity_id, "option": "option2"}
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(
        entity_id, "option2", {ATTR_OPTIONS: ["option1", "option2", "option3"]}
    )
    await hass.async_block_till_done()
    assert acc.select_chars["option1"].value is False
    assert acc.select_chars["option2"].value is True
    assert acc.select_chars["option3"].value is False

    hass.states.async_set(
        entity_id, "option3", {ATTR_OPTIONS: ["option1", "option2", "option3"]}
    )
    await hass.async_block_till_done()
    assert acc.select_chars["option1"].value is False
    assert acc.select_chars["option2"].value is False
    assert acc.select_chars["option3"].value is True

    hass.states.async_set(
        entity_id, "invalid", {ATTR_OPTIONS: ["option1", "option2", "option3"]}
    )
    await hass.async_block_till_done()
    assert acc.select_chars["option1"].value is False
    assert acc.select_chars["option2"].value is False
    assert acc.select_chars["option3"].value is False