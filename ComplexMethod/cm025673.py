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