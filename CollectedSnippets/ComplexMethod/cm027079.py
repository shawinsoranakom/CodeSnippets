async def _async_update_data(self) -> dict[str, AOSmithDevice]:
        """Fetch latest data from the device status endpoint."""
        try:
            devices = await self.client.get_devices()
        except AOSmithInvalidCredentialsException as err:
            raise ConfigEntryAuthFailed from err
        except AOSmithUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        mode_pending = any(device.status.mode_change_pending for device in devices)
        setpoint_pending = any(
            device.status.temperature_setpoint_pending for device in devices
        )

        if mode_pending or setpoint_pending:
            self.update_interval = FAST_INTERVAL
        else:
            self.update_interval = REGULAR_INTERVAL

        return {device.junction_id: device for device in devices}