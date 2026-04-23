async def test_dynamic_attributes(
    hass: HomeAssistant,
    multiple_climate_entities: tuple[str, str],
    request: pytest.FixtureRequest,
) -> None:
    """Test dynamic attributes."""
    entity_id, mock_fixture = multiple_climate_entities
    mock_instance = request.getfixturevalue(mock_fixture)
    await init_integration(hass)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == HVACMode.COOL

    mock_instance.get_power_on.return_value = False
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == HVACMode.OFF

    mock_instance.get_online.return_value = False
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == STATE_UNAVAILABLE

    mock_instance.get_power_on.return_value = True
    mock_instance.get_online.return_value = True
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == HVACMode.COOL

    mock_instance.get_mode.return_value = whirlpool.aircon.Mode.Heat
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == HVACMode.HEAT

    mock_instance.get_mode.return_value = whirlpool.aircon.Mode.Fan
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == HVACMode.FAN_ONLY

    mock_instance.get_fanspeed.return_value = whirlpool.aircon.FanSpeed.Auto
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.attributes[ATTR_FAN_MODE] == HVACMode.AUTO

    mock_instance.get_fanspeed.return_value = whirlpool.aircon.FanSpeed.Low
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.attributes[ATTR_FAN_MODE] == FAN_LOW

    mock_instance.get_fanspeed.return_value = whirlpool.aircon.FanSpeed.Medium
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.attributes[ATTR_FAN_MODE] == FAN_MEDIUM

    mock_instance.get_fanspeed.return_value = whirlpool.aircon.FanSpeed.High
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.attributes[ATTR_FAN_MODE] == FAN_HIGH

    mock_instance.get_fanspeed.return_value = whirlpool.aircon.FanSpeed.Off
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.attributes[ATTR_FAN_MODE] == FAN_OFF

    mock_instance.get_current_temp.return_value = 15
    mock_instance.get_temp.return_value = 20
    mock_instance.get_current_humidity.return_value = 80
    mock_instance.get_h_louver_swing.return_value = True
    attributes = (await update_ac_state(hass, entity_id, mock_instance)).attributes
    assert attributes[ATTR_CURRENT_TEMPERATURE] == 15
    assert attributes[ATTR_TEMPERATURE] == 20
    assert attributes[ATTR_CURRENT_HUMIDITY] == 80
    assert attributes[ATTR_SWING_MODE] == SWING_HORIZONTAL

    mock_instance.get_current_temp.return_value = 16
    mock_instance.get_temp.return_value = 21
    mock_instance.get_current_humidity.return_value = 70
    mock_instance.get_h_louver_swing.return_value = False
    attributes = (await update_ac_state(hass, entity_id, mock_instance)).attributes
    assert attributes[ATTR_CURRENT_TEMPERATURE] == 16
    assert attributes[ATTR_TEMPERATURE] == 21
    assert attributes[ATTR_CURRENT_HUMIDITY] == 70
    assert attributes[ATTR_SWING_MODE] == SWING_OFF