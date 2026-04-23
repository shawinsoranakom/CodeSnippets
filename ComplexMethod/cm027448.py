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