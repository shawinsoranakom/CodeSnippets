async def test_pressed_event(hass: HomeAssistant, mock_litejet) -> None:
    """Test handling an event from LiteJet."""

    await async_init_integration(hass, use_switch=True)

    # Switch 1
    mock_litejet.switch_pressed_callbacks[ENTITY_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    assert switch.is_on(hass, ENTITY_SWITCH)
    assert not switch.is_on(hass, ENTITY_OTHER_SWITCH)
    assert hass.states.get(ENTITY_SWITCH).state == STATE_ON
    assert hass.states.get(ENTITY_OTHER_SWITCH).state == STATE_OFF

    # Switch 2
    mock_litejet.switch_pressed_callbacks[ENTITY_OTHER_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    assert switch.is_on(hass, ENTITY_OTHER_SWITCH)
    assert switch.is_on(hass, ENTITY_SWITCH)
    assert hass.states.get(ENTITY_SWITCH).state == STATE_ON
    assert hass.states.get(ENTITY_OTHER_SWITCH).state == STATE_ON