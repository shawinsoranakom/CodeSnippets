async def async_migrate_entry(
    hass: HomeAssistant, config_entry: SatelConfigEntry
) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    # 1.2 Migrate subentries to include configured numbers to title
    if config_entry.version == 1 and config_entry.minor_version == 1:
        for subentry in config_entry.subentries.values():
            property_map = {
                SUBENTRY_TYPE_PARTITION: CONF_PARTITION_NUMBER,
                SUBENTRY_TYPE_ZONE: CONF_ZONE_NUMBER,
                SUBENTRY_TYPE_OUTPUT: CONF_OUTPUT_NUMBER,
                SUBENTRY_TYPE_SWITCHABLE_OUTPUT: CONF_SWITCHABLE_OUTPUT_NUMBER,
            }

            new_title = f"{subentry.title} ({subentry.data[property_map[subentry.subentry_type]]})"

            hass.config_entries.async_update_subentry(
                config_entry, subentry, title=new_title
            )

        hass.config_entries.async_update_entry(config_entry, minor_version=2)

    # 2.1 Migrate all entity unique IDs to replace "satel" prefix with config entry ID, allows multiple entries to be configured
    if config_entry.version == 1:

        @callback
        def migrate_unique_id(entity_entry: RegistryEntry) -> dict[str, str]:
            """Migrate the unique ID to a new format."""
            return {
                "new_unique_id": entity_entry.unique_id.replace(
                    "satel", config_entry.entry_id
                )
            }

        await async_migrate_entries(hass, config_entry.entry_id, migrate_unique_id)
        hass.config_entries.async_update_entry(config_entry, version=2, minor_version=1)

    # 2.2 Added encryption key to config entry data
    if config_entry.version == 2 and config_entry.minor_version < 2:
        new_data = {**config_entry.data, CONF_ENCRYPTION_KEY: None}

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, minor_version=2
        )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True