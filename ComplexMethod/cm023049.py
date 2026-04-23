async def test_modern_to_preset(hass: HomeAssistant, start_state) -> None:
    """Test modern fan state reproduction, switching to preset mode "Auto"."""
    hass.states.async_set(MODERN_FAN_ENTITY, "on", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)]
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(set_direction_calls) == 0
    assert len(oscillate_calls) == 0
    assert len(set_percentage_mode) == 0
    assert len(set_preset_mode) == 1
    assert set_preset_mode[0].domain == "fan"
    assert set_preset_mode[0].data == {
        "entity_id": MODERN_FAN_ENTITY,
        ATTR_PRESET_MODE: "Auto",
    }