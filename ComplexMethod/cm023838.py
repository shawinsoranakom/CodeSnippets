async def test_numbers_no_target_temp(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the number entities when target temperature is None."""
    state = hass.states.get("number.octoprint_extruder_temperature")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.name == "OctoPrint Extruder temperature"
    entry = entity_registry.async_get("number.octoprint_extruder_temperature")
    assert entry.unique_id == "uuid_tool0_temperature"

    state = hass.states.get("number.octoprint_bed_temperature")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.name == "OctoPrint Bed temperature"
    entry = entity_registry.async_get("number.octoprint_bed_temperature")
    assert entry.unique_id == "uuid_bed_temperature"