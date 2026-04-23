async def test_modern_turn_on_invalid(hass: HomeAssistant, start_state) -> None:
    """Test modern fan state reproduction, turning on with invalid state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    # Turn on with an invalid config (speed, percentage, preset_modes all None)
    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_INVALID_STATE)]
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "fan"
    assert turn_on_calls[0].data == {"entity_id": MODERN_FAN_ENTITY}

    assert len(turn_off_calls) == 0
    assert len(set_direction_calls) == 1
    assert set_direction_calls[0].domain == "fan"
    assert set_direction_calls[0].data == {
        "entity_id": MODERN_FAN_ENTITY,
        ATTR_DIRECTION: None,
    }
    assert len(oscillate_calls) == 1
    assert oscillate_calls[0].domain == "fan"
    assert oscillate_calls[0].data == {
        "entity_id": MODERN_FAN_ENTITY,
        ATTR_OSCILLATING: None,
    }
    assert len(set_percentage_mode) == 0
    assert len(set_preset_mode) == 0