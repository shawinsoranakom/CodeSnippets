async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        if not await self.point.update():
            raise UpdateFailed("Failed to fetch data from Point")

        if new_homes := set(self.point.homes) - self._known_homes:
            _LOGGER.debug("Found new homes: %s", new_homes)
            for home_id in new_homes:
                if self.new_home_callback:
                    self.new_home_callback(home_id)
            self._known_homes.update(new_homes)

        device_ids = {device.device_id for device in self.point.devices}
        if new_devices := device_ids - self._known_devices:
            _LOGGER.debug("Found new devices: %s", new_devices)
            for device_id in new_devices:
                for callback in self.new_device_callbacks:
                    callback(device_id)
            self._known_devices.update(new_devices)

        for device in self.point.devices:
            last_updated = parse_datetime(device.last_update)
            if (
                not last_updated
                or device.device_id not in self.device_updates
                or self.device_updates[device.device_id] < last_updated
            ):
                self.device_updates[device.device_id] = (
                    last_updated or datetime.fromtimestamp(0)
                )
                self.data[device.device_id] = {
                    k: await device.sensor(k)
                    for k in ("temperature", "humidity", "sound_pressure")
                }
        return self.data