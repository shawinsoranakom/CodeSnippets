def assert_thermostat_context_chain_events(
    events: list[dict[str, Any]], parent_context: Context
) -> None:
    """Assert the logbook events for a thermostat context chain.

    Verifies that climate and switch state changes have correct
    state, user attribution, and service call context.
    """
    climate_entries = [e for e in events if e.get("entity_id") == "climate.living_room"]
    assert len(climate_entries) == 1
    assert climate_entries[0]["state"] == "heat"
    assert climate_entries[0]["context_user_id"] == parent_context.user_id
    assert climate_entries[0]["context_event_type"] == EVENT_CALL_SERVICE
    assert climate_entries[0]["context_domain"] == "climate"
    assert climate_entries[0]["context_service"] == "set_hvac_mode"

    heater_entries = [e for e in events if e.get("entity_id") == "switch.heater"]
    assert len(heater_entries) == 1
    assert heater_entries[0]["state"] == "on"
    assert heater_entries[0]["context_user_id"] == parent_context.user_id
    assert heater_entries[0]["context_event_type"] == EVENT_CALL_SERVICE
    assert heater_entries[0]["context_domain"] == "homeassistant"
    assert heater_entries[0]["context_service"] == "turn_on"