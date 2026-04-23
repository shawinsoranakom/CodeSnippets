async def _async_update_data(self) -> FritzboxCoordinatorData:
        """Fetch all device data."""
        try:
            new_data = await self.hass.async_add_executor_job(
                self._update_fritz_devices
            )
        except (RequestConnectionError, HTTPError) as ex:
            LOGGER.debug(
                "Reload %s due to error '%s' to ensure proper re-login",
                self.config_entry.title,
                ex,
            )
            self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)
            raise UpdateFailed from ex

        for device in new_data.devices.values():
            # create device registry entry for new main devices
            if device.ain not in self.data.devices and (
                device.device_and_unit_id[1] is None
                or (
                    # workaround for sub units without a main device, e.g. Energy 250
                    # https://github.com/home-assistant/core/issues/145204
                    device.device_and_unit_id[1] == "1"
                    and device.device_and_unit_id[0] not in new_data.devices
                )
            ):
                dr.async_get(self.hass).async_get_or_create(
                    config_entry_id=self.config_entry.entry_id,
                    name=device.name,
                    identifiers={(DOMAIN, device.device_and_unit_id[0])},
                    manufacturer=device.manufacturer,
                    model=device.productname,
                    sw_version=device.fw_version,
                    configuration_url=self.configuration_url,
                )

        if (
            self.data.devices.keys() - new_data.devices.keys()
            or self.data.templates.keys() - new_data.templates.keys()
            or self.data.triggers.keys() - new_data.triggers.keys()
        ):
            self.cleanup_removed_devices(new_data)

        return new_data