async def test_is_closed_state_attribute(hass: HomeAssistant) -> None:
    """Test the behavior of the is_closed state attribute."""
    binary_valve = MockBinaryValveEntity()
    binary_valve.hass = hass

    assert binary_valve.state_attributes[ATTR_IS_CLOSED] is None

    binary_valve._attr_is_closed = True
    assert binary_valve.state_attributes[ATTR_IS_CLOSED] is True

    binary_valve._attr_is_closed = False
    assert binary_valve.state_attributes[ATTR_IS_CLOSED] is False

    pos_valve = MockValveEntity()
    pos_valve.hass = hass

    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is None

    # is_closed property is ignored for position reporting valves,
    # so it should remain None even if set to True
    pos_valve._attr_is_closed = True
    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is None

    # if current position is 0, the valve is closed
    pos_valve._attr_current_valve_position = 0
    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is True

    # if current position is greater than 0, the valve is not closed
    pos_valve._attr_current_valve_position = 1
    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is False
    pos_valve._attr_current_valve_position = 50
    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is False

    # if current position is None, the valve close state attribute
    # is unknown and no fallback to the is_closed property is done
    pos_valve._attr_current_valve_position = None
    assert pos_valve.state_attributes[ATTR_IS_CLOSED] is None