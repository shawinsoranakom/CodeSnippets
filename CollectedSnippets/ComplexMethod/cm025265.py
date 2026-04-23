async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Xbox Live friends."""
    presence = config_entry.runtime_data.presence
    if TYPE_CHECKING:
        assert config_entry.unique_id
    async_add_entities(
        [
            XboxSensorEntity(presence, config_entry.unique_id, description)
            for description in SENSOR_DESCRIPTIONS
            if check_deprecated_entity(
                hass, config_entry.unique_id, description, SENSOR_DOMAIN
            )
        ]
    )
    for subentry_id, subentry in config_entry.subentries.items():
        async_add_entities(
            [
                XboxSensorEntity(presence, subentry.unique_id, description)
                for description in SENSOR_DESCRIPTIONS
                if subentry.unique_id
                and check_deprecated_entity(
                    hass, subentry.unique_id, description, SENSOR_DOMAIN
                )
                and subentry.unique_id in presence.data.presence
                and subentry.subentry_type == "friend"
            ],
            config_subentry_id=subentry_id,
        )

    consoles = config_entry.runtime_data.consoles

    devices_added: set[str] = set()

    @callback
    def add_entities() -> None:
        nonlocal devices_added

        new_devices = set(consoles.data) - devices_added

        if new_devices:
            async_add_entities(
                [
                    XboxStorageDeviceSensorEntity(
                        consoles.data[console_id], storage_device, consoles, description
                    )
                    for description in STORAGE_SENSOR_DESCRIPTIONS
                    for console_id in new_devices
                    if (storage_devices := consoles.data[console_id].storage_devices)
                    for storage_device in storage_devices
                ]
            )
            devices_added |= new_devices
        devices_added &= set(consoles.data)

    config_entry.async_on_unload(consoles.async_add_listener(add_entities))
    add_entities()