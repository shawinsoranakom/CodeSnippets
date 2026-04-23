async def test_push_events(
    hass: HomeAssistant, mock_connected_snooz: SnoozFixture, snooz_fan_entity_id: str
) -> None:
    """Test state update events from snooz device."""
    mock_connected_snooz.device.trigger_state(SnoozDeviceState(False, 64))

    state = hass.states.get(snooz_fan_entity_id)
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PERCENTAGE] == 64

    mock_connected_snooz.device.trigger_state(SnoozDeviceState(True, 12))

    state = hass.states.get(snooz_fan_entity_id)
    assert ATTR_ASSUMED_STATE not in state.attributes
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PERCENTAGE] == 12

    mock_connected_snooz.device.trigger_disconnect()

    state = hass.states.get(snooz_fan_entity_id)
    assert state.attributes[ATTR_ASSUMED_STATE] is True

    # Don't attempt to reconnect
    await mock_connected_snooz.device.async_disconnect()