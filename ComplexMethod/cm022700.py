async def test_button_switch(
    hass: HomeAssistant, hk_driver, events: list[Event], domain
) -> None:
    """Test switch accessory from a (input) button entity."""
    entity_id = f"{domain}.test"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Switch(hass, hk_driver, "Switch", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.activate_only is True
    assert acc.char_on.value is False

    call_press = async_mock_service(hass, domain, "press")

    acc.char_on.client_update_value(True)
    await hass.async_block_till_done()
    assert acc.char_on.value is True
    assert len(call_press) == 1
    assert call_press[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    future = dt_util.utcnow() + timedelta(seconds=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    assert acc.char_on.value is True

    future = dt_util.utcnow() + timedelta(seconds=10)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()
    assert acc.char_on.value is False

    assert len(events) == 1
    assert len(call_press) == 1

    acc.char_on.client_update_value(False)
    await hass.async_block_till_done()
    assert acc.char_on.value is False
    assert len(events) == 1