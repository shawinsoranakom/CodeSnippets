def _generic_message(self, message: tuple) -> None:
        """Handle generic messages."""
        if (
            len(message) == 3
            and message[2] == "battery_level"
            and self.device_class == SensorDeviceClass.BATTERY
        ):
            self._value = message[1]
        elif len(message) == 3 and message[2] == "status":
            # Maybe the API wants to tell us, that the device went on- or offline.
            state = self._device_instance.is_online()
            if state != self.available and not state:
                _LOGGER.info(
                    "Device %s is unavailable",
                    self._device_instance.settings_property[
                        "general_device_settings"
                    ].name,
                )
            if state != self.available and state:
                _LOGGER.info(
                    "Device %s is back online",
                    self._device_instance.settings_property[
                        "general_device_settings"
                    ].name,
                )
            self._attr_available = state
        elif message[1] == "del" and self.platform.config_entry:
            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, self._device_instance.uid)}
            )
            if device:
                device_registry.async_update_device(
                    device.id,
                    remove_config_entry_id=self.platform.config_entry.entry_id,
                )
        else:
            _LOGGER.debug("No valid message received: %s", message)