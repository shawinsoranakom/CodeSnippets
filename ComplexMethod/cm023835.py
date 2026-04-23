async def test_sensors_no_target_temp(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the underlying sensors."""
    state = hass.states.get("sensor.octoprint_actual_tool1_temp")
    assert state is not None
    assert state.state == "18.83"
    assert state.name == "OctoPrint Actual tool1 temp"
    entry = entity_registry.async_get("sensor.octoprint_actual_tool1_temp")
    assert entry.unique_id == "actual tool1 temp-uuid"

    state = hass.states.get("sensor.octoprint_target_tool1_temp")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.name == "OctoPrint Target tool1 temp"
    entry = entity_registry.async_get("sensor.octoprint_target_tool1_temp")
    assert entry.unique_id == "target tool1 temp-uuid"

    state = hass.states.get("sensor.octoprint_current_file")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.name == "OctoPrint Current File"
    entry = entity_registry.async_get("sensor.octoprint_current_file")
    assert entry.unique_id == "Current File-uuid"

    state = hass.states.get("sensor.octoprint_current_file_size")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.name == "OctoPrint Current File Size"
    entry = entity_registry.async_get("sensor.octoprint_current_file_size")
    assert entry.unique_id == "Current File Size-uuid"