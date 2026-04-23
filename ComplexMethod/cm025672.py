async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: IottyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Activate the iotty Switch component."""
    _LOGGER.debug("Setup SWITCH entry id is %s", config_entry.entry_id)

    coordinator = config_entry.runtime_data.coordinator
    lightswitch_entities = [
        IottySwitch(
            coordinator=coordinator,
            iotty_cloud=coordinator.iotty,
            iotty_device=d,
            entity_description=ENTITIES[LS_DEVICE_TYPE_UID],
        )
        for d in coordinator.data.devices
        if d.device_type == LS_DEVICE_TYPE_UID
        if (isinstance(d, LightSwitch))
    ]
    _LOGGER.debug("Found %d LightSwitches", len(lightswitch_entities))

    outlet_entities = [
        IottySwitch(
            coordinator=coordinator,
            iotty_cloud=coordinator.iotty,
            iotty_device=d,
            entity_description=ENTITIES[OU_DEVICE_TYPE_UID],
        )
        for d in coordinator.data.devices
        if d.device_type == OU_DEVICE_TYPE_UID
        if (isinstance(d, Outlet))
    ]
    _LOGGER.debug("Found %d Outlets", len(outlet_entities))

    entities = lightswitch_entities + outlet_entities

    async_add_entities(entities)

    known_devices: set = config_entry.runtime_data.known_devices
    for known_device in coordinator.data.devices:
        if known_device.device_type in {LS_DEVICE_TYPE_UID, OU_DEVICE_TYPE_UID}:
            known_devices.add(known_device)

    @callback
    def async_update_data() -> None:
        """Handle updated data from the API endpoint."""
        if not coordinator.last_update_success:
            return

        devices = coordinator.data.devices
        entities = []
        known_devices: set = config_entry.runtime_data.known_devices

        # Add entities for devices which we've not yet seen
        for device in devices:
            if any(d.device_id == device.device_id for d in known_devices) or (
                device.device_type not in {LS_DEVICE_TYPE_UID, OU_DEVICE_TYPE_UID}
            ):
                continue

            iotty_entity: SwitchEntity
            iotty_device: LightSwitch | Outlet
            if device.device_type == LS_DEVICE_TYPE_UID:
                if TYPE_CHECKING:
                    assert isinstance(device, LightSwitch)
                iotty_device = LightSwitch(
                    device.device_id,
                    device.serial_number,
                    device.device_type,
                    device.device_name,
                )
            else:
                if TYPE_CHECKING:
                    assert isinstance(device, Outlet)
                iotty_device = Outlet(
                    device.device_id,
                    device.serial_number,
                    device.device_type,
                    device.device_name,
                )

            iotty_entity = IottySwitch(
                coordinator=coordinator,
                iotty_cloud=coordinator.iotty,
                iotty_device=iotty_device,
                entity_description=ENTITIES[device.device_type],
            )

            entities.extend([iotty_entity])
            known_devices.add(device)

        async_add_entities(entities)

    # Add a subscriber to the coordinator to discover new devices
    coordinator.async_add_listener(async_update_data)