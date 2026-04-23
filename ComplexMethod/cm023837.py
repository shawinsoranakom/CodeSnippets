async def test_sensors_printer_disconnected(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the underlying sensors."""
    state = hass.states.get("sensor.octoprint_job_percentage")
    assert state is not None
    assert state.state == "50"
    assert state.name == "OctoPrint Job Percentage"
    entry = entity_registry.async_get("sensor.octoprint_job_percentage")
    assert entry.unique_id == "Job Percentage-uuid"

    state = hass.states.get("sensor.octoprint_current_state")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.name == "OctoPrint Current State"
    entry = entity_registry.async_get("sensor.octoprint_current_state")
    assert entry.unique_id == "Current State-uuid"

    state = hass.states.get("sensor.octoprint_start_time")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.name == "OctoPrint Start Time"
    entry = entity_registry.async_get("sensor.octoprint_start_time")
    assert entry.unique_id == "Start Time-uuid"

    state = hass.states.get("sensor.octoprint_estimated_finish_time")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.name == "OctoPrint Estimated Finish Time"
    entry = entity_registry.async_get("sensor.octoprint_estimated_finish_time")
    assert entry.unique_id == "Estimated Finish Time-uuid"