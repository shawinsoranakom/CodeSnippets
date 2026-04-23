async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers."""
    triggers: list[dict[str, str]] = []
    entity_registry = er.async_get(hass)

    entries = [
        entry
        for entry in er.async_entries_for_device(entity_registry, device_id)
        if entry.domain == DOMAIN
    ]

    for entry in entries:
        device_class = get_device_class(hass, entry.entity_id) or DEVICE_CLASS_NONE
        state_class = get_capability(hass, entry.entity_id, ATTR_STATE_CLASS)
        unit_of_measurement = get_unit_of_measurement(hass, entry.entity_id)

        if not unit_of_measurement and not state_class:
            continue

        templates = ENTITY_TRIGGERS.get(
            device_class, ENTITY_TRIGGERS[DEVICE_CLASS_NONE]
        )

        triggers.extend(
            {
                **automation,
                "platform": "device",
                "device_id": device_id,
                "entity_id": entry.id,
                "domain": DOMAIN,
            }
            for automation in templates
        )

    return triggers