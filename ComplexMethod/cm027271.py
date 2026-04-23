async def async_migrate_integration(hass: HomeAssistant) -> None:
    """Migrate integration entry structure."""

    # Make sure we get enabled config entries first
    entries = sorted(
        hass.config_entries.async_entries(DOMAIN),
        key=lambda e: e.disabled_by is not None,
    )
    if not any(entry.version == 1 for entry in entries):
        return

    url_entries: dict[str, tuple[ConfigEntry, bool]] = {}
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    for entry in entries:
        use_existing = False
        # Create subentry with model from entry.data and options from entry.options
        subentry_data = entry.options.copy()
        subentry_data[CONF_MODEL] = entry.data[CONF_MODEL]

        subentry = ConfigSubentry(
            data=MappingProxyType(subentry_data),
            subentry_type="conversation",
            title=entry.title,
            unique_id=None,
        )
        if entry.data[CONF_URL] not in url_entries:
            use_existing = True
            all_disabled = all(
                e.disabled_by is not None
                for e in entries
                if e.data[CONF_URL] == entry.data[CONF_URL]
            )
            url_entries[entry.data[CONF_URL]] = (entry, all_disabled)

        parent_entry, all_disabled = url_entries[entry.data[CONF_URL]]

        hass.config_entries.async_add_subentry(parent_entry, subentry)

        conversation_entity_id = entity_registry.async_get_entity_id(
            "conversation",
            DOMAIN,
            entry.entry_id,
        )
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, entry.entry_id)}
        )

        if conversation_entity_id is not None:
            conversation_entity_entry = entity_registry.entities[conversation_entity_id]
            entity_disabled_by = conversation_entity_entry.disabled_by
            if (
                entity_disabled_by is er.RegistryEntryDisabler.CONFIG_ENTRY
                and not all_disabled
            ):
                # Device and entity registries will set the disabled_by flag to None
                # when moving a device or entity disabled by CONFIG_ENTRY to an enabled
                # config entry, but we want to set it to DEVICE or USER instead,
                entity_disabled_by = (
                    er.RegistryEntryDisabler.DEVICE
                    if device
                    else er.RegistryEntryDisabler.USER
                )
            entity_registry.async_update_entity(
                conversation_entity_id,
                config_entry_id=parent_entry.entry_id,
                config_subentry_id=subentry.subentry_id,
                disabled_by=entity_disabled_by,
                new_unique_id=subentry.subentry_id,
            )

        if device is not None:
            # Device and entity registries will set the disabled_by flag to None
            # when moving a device or entity disabled by CONFIG_ENTRY to an enabled
            # config entry, but we want to set it to USER instead,
            device_disabled_by = device.disabled_by
            if (
                device.disabled_by is dr.DeviceEntryDisabler.CONFIG_ENTRY
                and not all_disabled
            ):
                device_disabled_by = dr.DeviceEntryDisabler.USER
            device_registry.async_update_device(
                device.id,
                disabled_by=device_disabled_by,
                new_identifiers={(DOMAIN, subentry.subentry_id)},
                add_config_subentry_id=subentry.subentry_id,
                add_config_entry_id=parent_entry.entry_id,
            )
            if parent_entry.entry_id != entry.entry_id:
                device_registry.async_update_device(
                    device.id,
                    remove_config_entry_id=entry.entry_id,
                )
            else:
                device_registry.async_update_device(
                    device.id,
                    remove_config_entry_id=entry.entry_id,
                    remove_config_subentry_id=None,
                )

        if not use_existing:
            await hass.config_entries.async_remove(entry.entry_id)
        else:
            _add_ai_task_subentry(hass, entry)
            hass.config_entries.async_update_entry(
                entry,
                title=DEFAULT_NAME,
                # Update parent entry to only keep URL, remove model
                data={CONF_URL: entry.data[CONF_URL]},
                options={},
                version=3,
                minor_version=3,
            )