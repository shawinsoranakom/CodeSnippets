def _async_device_listener() -> None:
        """Add device entities."""
        received_devices = set(device_coordinator.data)
        new_devices = received_devices - current_devices
        old_devices = current_devices - received_devices
        if new_devices:
            device_registry = dr.async_get(hass)
            for device_id in new_devices:
                if device := device_registry.async_get_device({(DOMAIN, device_id)}):
                    if any(
                        (
                            config_entry := hass.config_entries.async_get_entry(
                                config_entry_id
                            )
                        )
                        and config_entry.state == ConfigEntryState.LOADED
                        for config_entry_id in device.config_entries
                    ):
                        continue
                async_add_entities(
                    WithingsDeviceSensor(device_coordinator, description, device_id)
                    for description in DEVICE_SENSORS
                )
                current_devices.add(device_id)

        if old_devices:
            device_registry = dr.async_get(hass)
            for device_id in old_devices:
                if device := device_registry.async_get_device({(DOMAIN, device_id)}):
                    device_registry.async_update_device(
                        device.id, remove_config_entry_id=entry.entry_id
                    )
                    current_devices.remove(device_id)