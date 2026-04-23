async def _async_update_data(self) -> dict[str, FujitsuHVAC]:
        """Fetch data from api endpoint."""
        listening_entities = set(self.async_contexts())
        try:
            if self.api.token_expired:
                await self.api.async_sign_in()

            if self.api.token_expiring_soon:
                await self.api.async_refresh_auth()

            devices = await self.api.async_get_devices()
        except AylaAuthError as e:
            raise ConfigEntryAuthFailed("Credentials expired for Ayla IoT API") from e

        if not listening_entities:
            devices = [
                dev
                for dev in devices
                if isinstance(dev, FujitsuHVAC) and dev.is_online()
            ]
        else:
            devices = [
                dev
                for dev in devices
                if dev.device_serial_number in listening_entities and dev.is_online()
            ]

        try:
            for dev in devices:
                await dev.async_update()
        except AylaAuthError as e:
            raise ConfigEntryAuthFailed("Credentials expired for Ayla IoT API") from e

        return {d.device_serial_number: d for d in devices}