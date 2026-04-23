async def test_modern_direction(hass: HomeAssistant) -> None:
    """Test modern fan state reproduction, switching only direction state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass,
        [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_PRESET_MODE_AUTO_REVERSE_STATE)],
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(set_direction_calls) == 1
    assert set_direction_calls[0].domain == "fan"
    assert set_direction_calls[0].data == {
        "entity_id": MODERN_FAN_ENTITY,
        ATTR_DIRECTION: DIRECTION_REVERSE,
    }
    assert len(oscillate_calls) == 0
    assert len(set_percentage_mode) == 0
    assert len(set_preset_mode) == 0