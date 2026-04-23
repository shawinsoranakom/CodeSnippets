def update_devices(self) -> None:
        """Update iCloud devices."""
        if self.api is None:
            return
        _LOGGER.debug("Updating devices")

        if self.api.requires_2fa:
            self._require_reauth()
            return

        api_devices = {}
        try:
            api_devices = self.api.devices
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Unknown iCloud error: %s", err)
            self._fetch_interval = 2
            dispatcher_send(self.hass, self.signal_device_update)
            self._schedule_next_fetch()
            return

        # Gets devices infos
        new_device = False
        for device in api_devices:
            status = device.status(DEVICE_STATUS_SET)
            device_id = status[DEVICE_ID]
            device_name = status[DEVICE_NAME]

            if (
                status[DEVICE_BATTERY_STATUS] == "Unknown"
                or status.get(DEVICE_BATTERY_LEVEL) is None
            ):
                continue

            if self._devices.get(device_id) is not None:
                # Seen device -> updating
                _LOGGER.debug("Updating iCloud device: %s", device_name)
                self._devices[device_id].update(status)
            else:
                # New device, should be unique
                _LOGGER.debug(
                    "Adding iCloud device: %s [model: %s]",
                    device_name,
                    status[DEVICE_RAW_DEVICE_MODEL],
                )
                self._devices[device_id] = IcloudDevice(self, device, status)
                self._devices[device_id].update(status)
                new_device = True

        if (
            DEVICE_STATUS_CODES.get(list(api_devices)[0][DEVICE_STATUS]) == "pending"
            and not self._retried_fetch
        ):
            _LOGGER.debug("Pending devices, trying again in 15s")
            self._fetch_interval = 0.25
            self._retried_fetch = True
        else:
            self._fetch_interval = self._determine_interval()
            self._retried_fetch = False

        dispatcher_send(self.hass, self.signal_device_update)
        if new_device:
            dispatcher_send(self.hass, self.signal_device_new)

        self._schedule_next_fetch()