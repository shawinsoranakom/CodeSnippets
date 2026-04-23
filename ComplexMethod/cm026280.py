async def _retrieve_encryption_key_from_dashboard(self) -> bool:
        """Try to retrieve the encryption key from the dashboard.

        Return boolean if a key was retrieved.
        """
        if (
            self._device_name is None
            or (manager := await async_get_or_create_dashboard_manager(self.hass))
            is None
            or (dashboard := manager.async_get()) is None
        ):
            return False

        await dashboard.async_request_refresh()
        if not dashboard.last_update_success:
            return False

        device = dashboard.data.get(self._device_name)

        if device is None:
            return False

        try:
            noise_psk = await dashboard.api.get_encryption_key(device["configuration"])
        except aiohttp.ClientError as err:
            _LOGGER.error("Error talking to the dashboard: %s", err)
            return False
        except json.JSONDecodeError:
            _LOGGER.exception("Error parsing response from dashboard")
            return False

        self._noise_psk = noise_psk
        return True