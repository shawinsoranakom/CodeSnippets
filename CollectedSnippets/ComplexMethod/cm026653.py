def async_determine_event_types(
    hass: HomeAssistant, entity_ids: list[str] | None, device_ids: list[str] | None
) -> set[EventType[Any] | str]:
    """Reduce the event types based on the entity ids and device ids."""
    logbook_config: LogbookConfig = hass.data[DOMAIN]
    external_events = logbook_config.external_events
    if not entity_ids and not device_ids:
        return {*BUILT_IN_EVENTS, *external_events}

    interested_domains: set[str] = set()
    for entry_id in _async_config_entries_for_ids(hass, entity_ids, device_ids):
        if entry := hass.config_entries.async_get_entry(entry_id):
            interested_domains.add(entry.domain)

    #
    # automations and scripts can refer to entities or devices
    # but they do not have a config entry so we need
    # to add them since we have historically included
    # them when matching only on entities
    #
    interested_event_types: set[EventType[Any] | str] = {
        external_event
        for external_event, domain_call in external_events.items()
        if domain_call[0] in interested_domains
    } | AUTOMATION_EVENTS
    if entity_ids:
        # We also allow entity_ids to be recorded via manual logbook entries.
        interested_event_types.add(EVENT_LOGBOOK_ENTRY)

    return interested_event_types