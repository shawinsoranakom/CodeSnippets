async def test_services(hass: HomeAssistant) -> None:
    """Test vacuum services."""
    # Test send_command
    send_command_calls = async_mock_service(hass, VACUUM_DOMAIN, SERVICE_SEND_COMMAND)

    params = {"rotate": 150, "speed": 20}
    await common.async_send_command(
        hass, "test_command", entity_id=ENTITY_VACUUM_BASIC, params=params
    )
    assert len(send_command_calls) == 1
    call = send_command_calls[-1]

    assert call.domain == VACUUM_DOMAIN
    assert call.service == SERVICE_SEND_COMMAND
    assert call.data[ATTR_ENTITY_ID] == ENTITY_VACUUM_BASIC
    assert call.data[ATTR_COMMAND] == "test_command"
    assert call.data[ATTR_PARAMS] == params

    # Test set fan speed
    set_fan_speed_calls = async_mock_service(hass, VACUUM_DOMAIN, SERVICE_SET_FAN_SPEED)

    await common.async_set_fan_speed(hass, FAN_SPEEDS[0], ENTITY_VACUUM_COMPLETE)
    assert len(set_fan_speed_calls) == 1
    call = set_fan_speed_calls[-1]

    assert call.domain == VACUUM_DOMAIN
    assert call.service == SERVICE_SET_FAN_SPEED
    assert call.data[ATTR_ENTITY_ID] == ENTITY_VACUUM_COMPLETE
    assert call.data[ATTR_FAN_SPEED] == FAN_SPEEDS[0]