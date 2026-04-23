async def _async_update_data(self) -> dict[str, DeviceSummary]:
        """Fetch the list of devices from the Fresh-r API."""
        username = self.config_entry.data[CONF_USERNAME]
        password = self.config_entry.data[CONF_PASSWORD]

        try:
            if not self.client.logged_in:
                await self.client.login(username, password)

            devices = await self.client.fetch_devices()
        except LoginError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except (ApiResponseError, ClientError) as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err

        current = {device.id: device for device in devices}

        if self.data is not None:
            stale_ids = set(self.data) - set(current)
            if stale_ids:
                device_registry = dr.async_get(self.hass)
                for device_id in stale_ids:
                    if device := device_registry.async_get_device(
                        identifiers={(DOMAIN, device_id)}
                    ):
                        device_registry.async_update_device(
                            device.id,
                            remove_config_entry_id=self.config_entry.entry_id,
                        )

        return current