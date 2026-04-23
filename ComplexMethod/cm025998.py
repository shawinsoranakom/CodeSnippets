async def _async_try_connect(
        self, host: str, serial: str | None = None, raise_on_progress: bool = True
    ) -> Light | None:
        """Try to connect."""
        self._async_abort_entries_match({CONF_HOST: host})
        connection = LIFXConnection(host, TARGET_ANY)
        try:
            await connection.async_setup()
        except socket.gaierror:
            return None
        device: Light = connection.device
        try:
            # get_hostfirmware required for MAC address offset
            # get_version required for lifx_features()
            # get_label required to log the name of the device
            # get_group required to populate suggested areas
            messages = await async_multi_execute_lifx_with_retries(
                [
                    device.get_hostfirmware,
                    device.get_version,
                    device.get_label,
                    device.get_group,
                ],
                DEFAULT_ATTEMPTS,
                OVERALL_TIMEOUT,
            )
        except TimeoutError:
            return None
        finally:
            connection.async_stop()
        if (
            messages is None
            or len(messages) != 4
            or lifx_features(device)["relays"] is True
            or device.host_firmware_version is None
        ):
            return None  # relays not supported
        # device.mac_addr is not the mac_address, its the serial number
        device.mac_addr = serial or messages[0].target_addr
        await self.async_set_unique_id(
            formatted_serial(device.mac_addr), raise_on_progress=raise_on_progress
        )
        return device