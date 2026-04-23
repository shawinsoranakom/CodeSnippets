async def async_migrate_entry(hass: HomeAssistant, entry: AirOSConfigEntry) -> bool:
    """Migrate old config entry."""

    # This means the user has downgraded from a future version
    if entry.version > 2:
        return False

    # 1.1 Migrate config_entry to add advanced ssl settings
    if entry.version == 1 and entry.minor_version == 1:
        new_minor_version = 2
        new_data = {**entry.data}
        advanced_data = {
            CONF_SSL: DEFAULT_SSL,
            CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        }
        new_data[SECTION_ADVANCED_SETTINGS] = advanced_data

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            minor_version=new_minor_version,
        )

    # 2.1 Migrate binary_sensor entity unique_id from device_id to mac_address
    #     Step 1 - migrate binary_sensor entity unique_id
    #     Step 2 - migrate device entity identifier
    if entry.version == 1:
        new_version = 2
        new_minor_version = 1

        mac_adress = dr.format_mac(entry.unique_id)

        device_registry = dr.async_get(hass)
        if device_entry := device_registry.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, mac_adress)}
        ):
            old_device_id = next(
                (
                    device_id
                    for domain, device_id in device_entry.identifiers
                    if domain == DOMAIN
                ),
            )

            @callback
            def update_unique_id(
                entity_entry: er.RegistryEntry,
            ) -> dict[str, str] | None:
                """Update unique id from device_id to mac address."""
                if old_device_id and entity_entry.unique_id.startswith(old_device_id):
                    suffix = entity_entry.unique_id.removeprefix(old_device_id)
                    new_unique_id = f"{mac_adress}{suffix}"
                    return {"new_unique_id": new_unique_id}
                return None

            await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)

            new_identifiers = device_entry.identifiers.copy()
            new_identifiers.discard((DOMAIN, old_device_id))
            new_identifiers.add((DOMAIN, mac_adress))
            device_registry.async_update_device(
                device_entry.id, new_identifiers=new_identifiers
            )

        hass.config_entries.async_update_entry(
            entry, version=new_version, minor_version=new_minor_version
        )

    return True