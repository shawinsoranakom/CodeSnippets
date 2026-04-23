async def _async_update_data(self) -> SensiboData:
        """Fetch data from Sensibo."""
        try:
            data = await self.client.async_get_devices_data()
        except AuthenticationError as error:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_error",
            ) from error
        except SensiboError as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_error",
                translation_placeholders={"error": str(error)},
            ) from error

        if not data.raw:
            raise UpdateFailed(translation_domain=DOMAIN, translation_key="no_data")

        current_devices = set(data.parsed)
        for device_data in data.parsed.values():
            if device_data.motion_sensors:
                for motion_sensor_id in device_data.motion_sensors:
                    current_devices.add(motion_sensor_id)

        if stale_devices := self.previous_devices - current_devices:
            LOGGER.debug("Removing stale devices: %s", stale_devices)
            device_registry = dr.async_get(self.hass)
            for _id in stale_devices:
                device = device_registry.async_get_device(identifiers={(DOMAIN, _id)})
                if device:
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )
        self.previous_devices = current_devices

        return data