def _setup(self) -> bool:
        """Set up a Netgear router sync portion."""
        self.api = get_api(
            self._password,
            self._host,
            self._username,
            self._port,
            self._ssl,
        )

        self._info = self.api.get_info()
        if self._info is None:
            return False

        self.device_name = self._info.get("DeviceName", DEFAULT_NAME)
        self.model = self._info.get("ModelName")
        self.firmware_version = self._info.get("Firmwareversion")
        self.hardware_version = self._info.get("Hardwareversion")
        self.serial_number = self._info["SerialNumber"]
        self.mode = self._info.get("DeviceMode", MODE_ROUTER)

        enabled_entries = [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.disabled_by is None
        ]
        self.track_devices = self.mode == MODE_ROUTER or len(enabled_entries) == 1
        _LOGGER.debug(
            "Netgear track_devices = '%s', device mode '%s'",
            self.track_devices,
            self.mode,
        )

        for model in MODELS_V2:
            if self.model.startswith(model):
                self.method_version = 2

        if self.method_version == 2 and self.track_devices:
            if not self.api.get_attached_devices_2():
                _LOGGER.error(
                    (
                        "Netgear Model '%s' in MODELS_V2 list, but failed to get"
                        " attached devices using V2"
                    ),
                    self.model,
                )
                self.method_version = 1

        return True