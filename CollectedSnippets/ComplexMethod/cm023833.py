async def test_sensors_printer_offline(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the underlying sensors when the printer is offline."""
    state = hass.states.get("binary_sensor.octoprint_printing")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.name == "OctoPrint Printing"
    entry = entity_registry.async_get("binary_sensor.octoprint_printing")
    assert entry.unique_id == "Printing-uuid"

    state = hass.states.get("binary_sensor.octoprint_printing_error")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.name == "OctoPrint Printing Error"
    entry = entity_registry.async_get("binary_sensor.octoprint_printing_error")
    assert entry.unique_id == "Printing Error-uuid"