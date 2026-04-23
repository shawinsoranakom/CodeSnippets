async def test_activated_event(hass: HomeAssistant, mock_litejet) -> None:
    """Test handling an event from LiteJet."""

    await async_init_integration(hass)

    # Light 1
    mock_litejet.get_load_level.return_value = 99
    mock_litejet.get_load_level.reset_mock()
    mock_litejet.load_activated_callbacks[ENTITY_LIGHT_NUMBER](99)
    await hass.async_block_till_done()

    mock_litejet.get_load_level.assert_called_once_with(ENTITY_LIGHT_NUMBER)

    assert light.is_on(hass, ENTITY_LIGHT)
    assert not light.is_on(hass, ENTITY_OTHER_LIGHT)
    assert hass.states.get(ENTITY_LIGHT).state == "on"
    assert hass.states.get(ENTITY_OTHER_LIGHT).state == "off"
    assert hass.states.get(ENTITY_LIGHT).attributes.get(ATTR_BRIGHTNESS) == 255

    # Light 2

    mock_litejet.get_load_level.return_value = 40
    mock_litejet.get_load_level.reset_mock()
    mock_litejet.load_activated_callbacks[ENTITY_OTHER_LIGHT_NUMBER](40)
    await hass.async_block_till_done()

    mock_litejet.get_load_level.assert_called_once_with(ENTITY_OTHER_LIGHT_NUMBER)

    assert light.is_on(hass, ENTITY_LIGHT)
    assert light.is_on(hass, ENTITY_OTHER_LIGHT)
    assert hass.states.get(ENTITY_LIGHT).state == "on"
    assert hass.states.get(ENTITY_OTHER_LIGHT).state == "on"
    assert hass.states.get(ENTITY_OTHER_LIGHT).attributes.get(ATTR_BRIGHTNESS) == 103