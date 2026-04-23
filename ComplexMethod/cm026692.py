async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BeoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Event entities from config entry."""
    entities: list[BeoEvent] = [
        BeoButtonEvent(config_entry, button_type)
        for button_type in get_device_buttons(config_entry.data[CONF_MODEL])
    ]

    # Check for connected Beoremote One
    remotes = await get_remotes(config_entry.runtime_data.client)

    for remote in remotes:
        entities.extend(
            [
                BeoRemoteKeyEvent(config_entry, remote, key_type)
                for key_type in get_remote_keys()
            ]
        )

    # If the remote is no longer available, then delete the device.
    # The remote may appear as being available to the device after it has been unpaired on the remote
    # As it has to be removed from the device on the app.

    device_registry = dr.async_get(hass)
    devices = device_registry.devices.get_devices_for_config_entry_id(
        config_entry.entry_id
    )
    for device in devices:
        if device.model == BeoModel.BEOREMOTE_ONE and device.serial_number not in {
            remote.serial_number for remote in remotes
        }:
            device_registry.async_update_device(
                device.id, remove_config_entry_id=config_entry.entry_id
            )

    async_add_entities(new_entities=entities)