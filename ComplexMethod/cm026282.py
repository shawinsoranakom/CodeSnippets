async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        if self._install_lock.locked():
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ota_in_progress",
                translation_placeholders={
                    "configuration": self._device_info.name,
                },
            )

        # Ensure only one OTA per device at a time
        async with self._install_lock:
            # Ensure only one compile at a time for ALL devices
            async with self.hass.data.setdefault(KEY_UPDATE_LOCK, asyncio.Lock()):
                coordinator = self.coordinator
                api = coordinator.api
                device = coordinator.data.get(self._device_info.name)
                assert device is not None
                configuration = device["configuration"]
                if not await api.compile(configuration):
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="error_compiling",
                        translation_placeholders={
                            "configuration": configuration,
                        },
                    )

            # If the device uses deep sleep, there's a small chance it goes
            # to sleep right after the dashboard connects but before the OTA
            # starts. In that case, the update won't go through, so we try
            # again to catch it on its next wakeup.
            attempts = 2 if self._device_info.has_deep_sleep else 1
            try:
                for attempt in range(1, attempts + 1):
                    await self._async_wait_available()
                    if await api.upload(configuration, "OTA"):
                        break
                    if attempt == attempts:
                        raise HomeAssistantError(
                            translation_domain=DOMAIN,
                            translation_key="error_uploading",
                            translation_placeholders={
                                "configuration": configuration,
                            },
                        )
            finally:
                await self.coordinator.async_request_refresh()