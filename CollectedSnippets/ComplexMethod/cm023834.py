async def test_sensors(
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
    assert state.state == "operational"
    assert state.name == "OctoPrint Current State"
    entry = entity_registry.async_get("sensor.octoprint_current_state")
    assert entry.unique_id == "Current State-uuid"

    state = hass.states.get("sensor.octoprint_actual_tool1_temp")
    assert state is not None
    assert state.state == "18.83"
    assert state.name == "OctoPrint Actual tool1 temp"
    entry = entity_registry.async_get("sensor.octoprint_actual_tool1_temp")
    assert entry.unique_id == "actual tool1 temp-uuid"

    state = hass.states.get("sensor.octoprint_target_tool1_temp")
    assert state is not None
    assert state.state == "37.83"
    assert state.name == "OctoPrint Target tool1 temp"
    entry = entity_registry.async_get("sensor.octoprint_target_tool1_temp")
    assert entry.unique_id == "target tool1 temp-uuid"

    state = hass.states.get("sensor.octoprint_target_tool1_temp")
    assert state is not None
    assert state.state == "37.83"
    assert state.name == "OctoPrint Target tool1 temp"
    entry = entity_registry.async_get("sensor.octoprint_target_tool1_temp")
    assert entry.unique_id == "target tool1 temp-uuid"

    state = hass.states.get("sensor.octoprint_start_time")
    assert state is not None
    assert state.state == "2020-02-20T09:00:00+00:00"
    assert state.name == "OctoPrint Start Time"
    entry = entity_registry.async_get("sensor.octoprint_start_time")
    assert entry.unique_id == "Start Time-uuid"

    state = hass.states.get("sensor.octoprint_estimated_finish_time")
    assert state is not None
    assert state.state == "2020-02-20T10:50:00+00:00"
    assert state.name == "OctoPrint Estimated Finish Time"
    entry = entity_registry.async_get("sensor.octoprint_estimated_finish_time")
    assert entry.unique_id == "Estimated Finish Time-uuid"

    state = hass.states.get("sensor.octoprint_current_file")
    assert state is not None
    assert state.state == "Test_File_Name.gcode"
    assert state.name == "OctoPrint Current File"
    entry = entity_registry.async_get("sensor.octoprint_current_file")
    assert entry.unique_id == "Current File-uuid"

    state = hass.states.get("sensor.octoprint_current_file_size")
    assert state is not None
    assert state.state == "123.456789"
    assert state.attributes.get("unit_of_measurement") == UnitOfInformation.MEGABYTES
    assert state.name == "OctoPrint Current File Size"
    entry = entity_registry.async_get("sensor.octoprint_current_file_size")
    assert entry.unique_id == "Current File Size-uuid"