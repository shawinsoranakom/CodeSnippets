async def _async_update_data(self) -> IottyData:
        """Fetch data from iottyCloud device."""
        _LOGGER.debug("Fetching devices status from iottyCloud")

        current_devices = await self.iotty.get_devices()

        removed_devices = [
            d
            for d in self._devices
            if not any(x.device_id == d.device_id for x in current_devices)
        ]

        for removed_device in removed_devices:
            device_to_remove = self._device_registry.async_get_device(
                {(DOMAIN, removed_device.device_id)}
            )
            if device_to_remove is not None:
                self._device_registry.async_remove_device(device_to_remove.id)

        self._devices = current_devices

        for device in self._devices:
            res = await self.iotty.get_status(device.device_id)
            json = res.get(RESULT, {})
            if (
                not isinstance(res, dict)
                or RESULT not in res
                or not isinstance(json := res[RESULT], dict)
                or not (status := json.get(STATUS))
            ):
                _LOGGER.warning("Unable to read status for device %s", device.device_id)
            else:
                _LOGGER.debug(
                    "Retrieved status: '%s' for device %s", status, device.device_id
                )
                device.update_status(status)
                if isinstance(device, Shutter) and isinstance(
                    percentage := json.get(OPEN_PERCENTAGE), int
                ):
                    device.update_percentage(percentage)

        return IottyData(self._devices)