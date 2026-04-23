def _async_add_remove_devices(self, inverter_data: dict[int, InverterData]) -> None:
        """Add new devices, remove non-existing devices."""

        if (
            current_devices := {
                (k, self.solarlog.device_name(k)) for k in inverter_data
            }
        ) == self._devices_last_update:
            return

        # remove old devices
        if removed_devices := self._devices_last_update - current_devices:
            _LOGGER.info("Removed device(s): %s", ", ".join(map(str, removed_devices)))
            device_registry = dr.async_get(self.hass)

            for removed_device in removed_devices:
                device_name = ""
                for did, dn in self._devices_last_update:
                    if did == removed_device[0]:
                        device_name = dn
                        break
                if device := device_registry.async_get_device(
                    identifiers={
                        (
                            DOMAIN,
                            f"{self.config_entry.entry_id}_{slugify(device_name)}",
                        )
                    }
                ):
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )
                    _LOGGER.info("Device removed from device registry: %s", device.id)

        # add new devices
        if new_devices := current_devices - self._devices_last_update:
            _LOGGER.info("New device(s) found: %s", ", ".join(map(str, new_devices)))
            for device_id in new_devices:
                for callback in self.new_device_callbacks:
                    callback(device_id[0])

        self._devices_last_update = current_devices