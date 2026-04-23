def migrate_config_entry_and_identifiers(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Migrate old non-unique identifiers to new unique identifiers."""

    related_device_flag: bool
    device_id: str

    device_reg = dr.async_get(hass)
    # Get all devices associated to contextual gateway config_entry
    # and loop through list of devices.
    for device in dr.async_entries_for_config_entry(device_reg, config_entry.entry_id):
        related_device_flag = False
        for identifier in device.identifiers:
            if identifier[0] != DOMAIN:
                continue

            related_device_flag = True

            _id = identifier[1]

            # Identify gateway device.
            if _id == config_entry.data[CONF_GATEWAY_ID]:
                # Using this to avoid updating gateway's own device registry entry
                related_device_flag = False
                break

            device_id = str(_id)
            break

        # Check that device is related to tradfri domain (and is not the gateway itself)
        if not related_device_flag:
            continue

        # Loop through list of config_entry_ids for device
        config_entry_ids = device.config_entries
        for config_entry_id in config_entry_ids:
            # Check that the config entry in list is not the device's primary config entry
            if config_entry_id == device.primary_config_entry:
                continue

            # Check that the 'other' config entry is also a tradfri config entry
            other_entry = hass.config_entries.async_get_entry(config_entry_id)

            if other_entry is None or other_entry.domain != DOMAIN:
                continue

            # Remove non-primary 'tradfri' config entry from device's config_entry_ids
            device_reg.async_update_device(
                device.id, remove_config_entry_id=config_entry_id
            )

        if config_entry.data[CONF_GATEWAY_ID] in device_id:
            continue

        device_reg.async_update_device(
            device.id,
            new_identifiers={
                (DOMAIN, f"{config_entry.data[CONF_GATEWAY_ID]}-{device_id}")
            },
        )