async def async_setup_entry(
    hass: HomeAssistant,
    entry: SynologyDSMConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Synology NAS Sensor."""
    data = entry.runtime_data
    api = data.api
    coordinator = data.coordinator_central
    storage = api.storage
    if TYPE_CHECKING:
        assert storage is not None
    known_usb_devices: set[str] = set()

    def _check_usb_devices() -> None:
        """Check for new USB devices during and after initial setup."""
        if api.external_usb is not None and api.external_usb.get_devices:
            current_usb_devices: set[str] = {
                device.device_name for device in api.external_usb.get_devices.values()
            }
            new_usb_devices = current_usb_devices - known_usb_devices
            if new_usb_devices:
                known_usb_devices.update(new_usb_devices)
                external_devices: list[SynoCoreExternalUSBDevice] = [
                    device
                    for device in api.external_usb.get_devices.values()
                    if device.device_name in new_usb_devices
                ]
                new_usb_entities: list[SynoDSMExternalUSBSensor] = [
                    SynoDSMExternalUSBSensor(
                        api, coordinator, description, device.device_name
                    )
                    for device in entry.data.get(CONF_DEVICES, external_devices)
                    for description in EXTERNAL_USB_DISK_SENSORS
                ]
                new_usb_entities.extend(
                    [
                        SynoDSMExternalUSBSensor(
                            api, coordinator, description, partition.partition_title
                        )
                        for device in entry.data.get(CONF_DEVICES, external_devices)
                        for partition in device.device_partitions.values()
                        for description in EXTERNAL_USB_PARTITION_SENSORS
                    ]
                )
                async_add_entities(new_usb_entities)

    entities: list[SynoDSMUtilSensor | SynoDSMStorageSensor | SynoDSMInfoSensor] = [
        SynoDSMUtilSensor(api, coordinator, description)
        for description in UTILISATION_SENSORS
    ]

    # Handle all volumes
    if storage.volumes_ids:
        entities.extend(
            [
                SynoDSMStorageSensor(api, coordinator, description, volume)
                for volume in entry.data.get(CONF_VOLUMES, storage.volumes_ids)
                for description in STORAGE_VOL_SENSORS
            ]
        )

    # Handle all disks
    if storage.disks_ids:
        entities.extend(
            [
                SynoDSMStorageSensor(api, coordinator, description, disk)
                for disk in entry.data.get(CONF_DISKS, storage.disks_ids)
                for description in STORAGE_DISK_SENSORS
            ]
        )

    entities.extend(
        [
            SynoDSMInfoSensor(api, coordinator, description)
            for description in INFORMATION_SENSORS
        ]
    )

    _check_usb_devices()
    entry.async_on_unload(coordinator.async_add_listener(_check_usb_devices))

    async_add_entities(entities)