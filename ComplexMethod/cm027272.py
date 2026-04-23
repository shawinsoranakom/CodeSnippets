async def async_migrate_entry(hass: HomeAssistant, entry: OllamaConfigEntry) -> bool:
    """Migrate entry."""
    _LOGGER.debug("Migrating from version %s:%s", entry.version, entry.minor_version)

    if entry.version > 3:
        # This means the user has downgraded from a future version
        return False

    if entry.version == 2 and entry.minor_version == 1:
        # Correct broken device migration in Home Assistant Core 2025.7.0b0-2025.7.0b1
        device_registry = dr.async_get(hass)
        for device in dr.async_entries_for_config_entry(
            device_registry, entry.entry_id
        ):
            device_registry.async_update_device(
                device.id,
                remove_config_entry_id=entry.entry_id,
                remove_config_subentry_id=None,
            )

        hass.config_entries.async_update_entry(entry, minor_version=2)

    if entry.version == 2 and entry.minor_version == 2:
        # Update subentries to include the model
        for subentry in entry.subentries.values():
            if subentry.subentry_type == "conversation":
                updated_data = dict(subentry.data)
                updated_data[CONF_MODEL] = entry.data[CONF_MODEL]

                hass.config_entries.async_update_subentry(
                    entry, subentry, data=MappingProxyType(updated_data)
                )

        # Update main entry to remove model and bump version
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_URL: entry.data[CONF_URL]},
            version=3,
            minor_version=1,
        )

    if entry.version == 3 and entry.minor_version == 1:
        _add_ai_task_subentry(hass, entry)
        hass.config_entries.async_update_entry(entry, minor_version=2)

    if entry.version == 3 and entry.minor_version == 2:
        # Fix migration where the disabled_by flag was not set correctly.
        # We can currently only correct this for enabled config entries,
        # because migration does not run for disabled config entries. This
        # is asserted in tests, and if that behavior is changed, we should
        # correct also disabled config entries.
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        entity_entries = er.async_entries_for_config_entry(
            entity_registry, entry.entry_id
        )
        if entry.disabled_by is None:
            # If the config entry is not disabled, we need to set the disabled_by
            # flag on devices to USER, and on entities to DEVICE, if they are set
            # to CONFIG_ENTRY.
            for device in devices:
                if device.disabled_by is not dr.DeviceEntryDisabler.CONFIG_ENTRY:
                    continue
                device_registry.async_update_device(
                    device.id,
                    disabled_by=dr.DeviceEntryDisabler.USER,
                )
            for entity in entity_entries:
                if entity.disabled_by is not er.RegistryEntryDisabler.CONFIG_ENTRY:
                    continue
                entity_registry.async_update_entity(
                    entity.entity_id,
                    disabled_by=er.RegistryEntryDisabler.DEVICE,
                )
        hass.config_entries.async_update_entry(entry, minor_version=3)

    _LOGGER.debug(
        "Migration to version %s:%s successful", entry.version, entry.minor_version
    )

    return True