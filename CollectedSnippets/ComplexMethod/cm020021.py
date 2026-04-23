async def test_updating(
    hass: HomeAssistant,
    mock_niko_home_control_connection: AsyncMock,
    mock_config_entry: MockConfigEntry,
    light: AsyncMock,
    dimmable_light: AsyncMock,
) -> None:
    """Test turning on the light."""
    await setup_integration(hass, mock_config_entry)

    assert hass.states.get("light.light").state == STATE_ON

    light.state = 0
    await find_update_callback(mock_niko_home_control_connection, 1)(0)
    await hass.async_block_till_done()

    assert hass.states.get("light.light").state == STATE_OFF

    assert hass.states.get("light.dimmable_light").state == STATE_ON
    assert hass.states.get("light.dimmable_light").attributes[ATTR_BRIGHTNESS] == 100

    dimmable_light.state = 204
    await find_update_callback(mock_niko_home_control_connection, 2)(204)
    await hass.async_block_till_done()

    assert hass.states.get("light.dimmable_light").state == STATE_ON
    assert hass.states.get("light.dimmable_light").attributes[ATTR_BRIGHTNESS] == 204

    dimmable_light.state = 0
    await find_update_callback(mock_niko_home_control_connection, 2)(0)
    await hass.async_block_till_done()

    assert hass.states.get("light.dimmable_light").state == STATE_OFF
    assert hass.states.get("light.dimmable_light").attributes[ATTR_BRIGHTNESS] is None