def _async_add_remove_devices(self) -> None:
        """Add new devices and remove orphaned devices from the registry."""
        current_devices = set(self.data)
        device_registry = dr.async_get(self.hass)

        registered_devices: set[str] = {
            str(mower_id)
            for device in device_registry.devices.get_devices_for_config_entry_id(
                self.config_entry.entry_id
            )
            for domain, mower_id in device.identifiers
            if domain == DOMAIN
        }

        orphaned_devices = registered_devices - current_devices
        if orphaned_devices:
            _LOGGER.debug("Removing orphaned devices: %s", orphaned_devices)
            device_registry = dr.async_get(self.hass)
            for mower_id in orphaned_devices:
                dev = device_registry.async_get_device(identifiers={(DOMAIN, mower_id)})
                if dev is not None:
                    device_registry.async_update_device(
                        device_id=dev.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )

        new_devices = current_devices - registered_devices
        if new_devices:
            _LOGGER.debug("New devices found: %s", new_devices)
            for mower_callback in self.new_devices_callbacks:
                mower_callback(new_devices)