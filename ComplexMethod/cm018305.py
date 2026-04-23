async def test_fan_available(
    hass: HomeAssistant,
    command_store: CommandStore,
    device: Device,
) -> None:
    """Test fan available property."""
    entity_id = "fan.test"
    await setup_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_PERCENTAGE] == 18
    assert state.attributes[ATTR_PERCENTAGE_STEP] == pytest.approx(2.040816)
    assert state.attributes[ATTR_PRESET_MODES] == ["Auto"]
    assert state.attributes[ATTR_PRESET_MODE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 57

    await command_store.trigger_observe_callback(
        hass, device, {ATTR_REACHABLE_STATE: 0}
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE