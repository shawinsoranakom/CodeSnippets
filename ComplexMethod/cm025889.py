async def async_unload_entry(
    hass: HomeAssistant, config_entry: DenonavrConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if config_entry.options.get(CONF_USE_TELNET, DEFAULT_USE_TELNET):
        receiver = config_entry.runtime_data
        await receiver.async_telnet_disconnect()

    # Remove zone2 and zone3 entities if needed
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    unique_id = config_entry.unique_id or config_entry.entry_id
    zone2_id = f"{unique_id}-Zone2"
    zone3_id = f"{unique_id}-Zone3"
    for entry in entries:
        if entry.unique_id == zone2_id and not config_entry.options.get(CONF_ZONE2):
            entity_registry.async_remove(entry.entity_id)
            _LOGGER.debug("Removing zone2 from DenonAvr")
        if entry.unique_id == zone3_id and not config_entry.options.get(CONF_ZONE3):
            entity_registry.async_remove(entry.entity_id)
            _LOGGER.debug("Removing zone3 from DenonAvr")

    return unload_ok