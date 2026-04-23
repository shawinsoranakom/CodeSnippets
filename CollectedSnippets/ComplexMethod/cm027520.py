def determine_machine_type(
    hass: HomeAssistant,
    entry_id: str,
    device_id: str,
) -> Capability | None:
    """Determine the machine type for a device."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, entry_id)
    device_entries = [entry for entry in entries if device_id in entry.unique_id]
    for entry in device_entries:
        if Attribute.DISHWASHER_JOB_STATE in entry.unique_id:
            return Capability.DISHWASHER_OPERATING_STATE
        if Attribute.WASHER_JOB_STATE in entry.unique_id:
            return Capability.WASHER_OPERATING_STATE
        if Attribute.DRYER_JOB_STATE in entry.unique_id:
            return Capability.DRYER_OPERATING_STATE
        if Attribute.OVEN_JOB_STATE in entry.unique_id:
            return Capability.OVEN_OPERATING_STATE
    return None