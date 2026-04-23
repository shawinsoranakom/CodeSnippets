async def update_devices(self) -> None:
        """Update AsusWrt devices tracker."""
        new_device = False
        _LOGGER.debug("Checking devices for ASUS router %s", self.host)
        try:
            wrt_devices = await self._api.async_get_connected_devices()
        except (OSError, AsusRouterError) as exc:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to ASUS router %s for device update: %s",
                    self.host,
                    exc,
                )
            return

        if self._connect_error:
            self._connect_error = False
            _LOGGER.warning("Reconnected to ASUS router %s", self.host)

        self._connected_devices = len(wrt_devices)
        consider_home = int(
            self._options.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME.total_seconds())
        )
        track_unknown = self._options.get(CONF_TRACK_UNKNOWN, DEFAULT_TRACK_UNKNOWN)

        for device_mac, device in self._devices.items():
            dev_info = wrt_devices.pop(device_mac, None)
            device.update(dev_info, consider_home)

        for device_mac, dev_info in wrt_devices.items():
            if not track_unknown and not dev_info.name:
                continue
            new_device = True
            device = AsusWrtDevInfo(device_mac)
            device.update(dev_info)
            self._devices[device_mac] = device

        async_dispatcher_send(self.hass, self.signal_device_update)
        if new_device:
            async_dispatcher_send(self.hass, self.signal_device_new)
        await self._update_unpolled_sensors()