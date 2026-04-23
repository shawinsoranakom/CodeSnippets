async def async_migrate_unique_id(
    hass: HomeAssistant, config_entry: DaikinConfigEntry, device: Appliance
) -> None:
    """Migrate old entry."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    old_unique_id = config_entry.unique_id
    new_unique_id = device.mac
    new_mac = dr.format_mac(new_unique_id)
    new_name = device.values.get("name", "Daikin AC")

    @callback
    def _update_unique_id(entity_entry: er.RegistryEntry) -> dict[str, str] | None:
        """Update unique ID of entity entry."""
        return update_unique_id(entity_entry, new_unique_id)

    if new_unique_id == old_unique_id:
        return

    duplicate = dev_reg.async_get_device(
        connections={(CONNECTION_NETWORK_MAC, new_mac)}, identifiers=None
    )

    # Remove duplicated device
    if duplicate is not None:
        if config_entry.entry_id in duplicate.config_entries:
            _LOGGER.debug(
                "Removing duplicated device %s",
                duplicate.name,
            )

            # The automatic cleanup in entity registry is scheduled as a task, remove
            # the entities manually to avoid unique_id collision when the entities
            # are migrated.
            duplicate_entities = er.async_entries_for_device(
                ent_reg, duplicate.id, True
            )
            for entity in duplicate_entities:
                if entity.config_entry_id == config_entry.entry_id:
                    ent_reg.async_remove(entity.entity_id)

            dev_reg.async_update_device(
                duplicate.id, remove_config_entry_id=config_entry.entry_id
            )

    # Migrate devices
    for device_entry in dr.async_entries_for_config_entry(
        dev_reg, config_entry.entry_id
    ):
        for connection in device_entry.connections:
            if connection[1] == old_unique_id:
                new_connections = {(CONNECTION_NETWORK_MAC, new_mac)}

                _LOGGER.debug(
                    "Migrating device %s connections to %s",
                    device_entry.name,
                    new_connections,
                )
                dev_reg.async_update_device(
                    device_entry.id,
                    merge_connections=new_connections,
                )

        if device_entry.name is None:
            _LOGGER.debug(
                "Migrating device name to %s",
                new_name,
            )
            dev_reg.async_update_device(
                device_entry.id,
                name=new_name,
            )

        # Migrate entities
        await er.async_migrate_entries(hass, config_entry.entry_id, _update_unique_id)

        new_data = {**config_entry.data, KEY_MAC: dr.format_mac(new_unique_id)}

        hass.config_entries.async_update_entry(
            config_entry, unique_id=new_unique_id, data=new_data
        )