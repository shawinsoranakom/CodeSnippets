async def async_discover_motionblind(self, mac_code: str) -> None:
        """Discover Motionblinds initialized by the user."""
        if not is_valid_mac(mac_code):
            _LOGGER.error("Invalid MAC code: %s", mac_code.upper())
            raise InvalidMACCode

        scanner_count = bluetooth.async_scanner_count(self.hass, connectable=True)
        if not scanner_count:
            _LOGGER.error("No bluetooth adapter found")
            raise NoBluetoothAdapter

        bleak_scanner = bluetooth.async_get_scanner(self.hass)
        devices = await bleak_scanner.discover()

        if len(devices) == 0:
            _LOGGER.error("Could not find any bluetooth devices")
            raise NoDevicesFound

        motion_device: BLEDevice | None = next(
            (
                device
                for device in devices
                if device
                and device.name
                and f"MOTION_{mac_code.upper()}" in device.name
            ),
            None,
        )

        if motion_device is None:
            _LOGGER.error("Could not find a motor with MAC code: %s", mac_code.upper())
            raise CouldNotFindMotor

        await self.async_set_unique_id(motion_device.address, raise_on_progress=False)
        self._abort_if_unique_id_configured()

        self._discovery_info = motion_device
        self._mac_code = mac_code.upper()
        self._display_name = DISPLAY_NAME.format(mac_code=self._mac_code)