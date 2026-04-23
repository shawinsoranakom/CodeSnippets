async def _async_update_data(self) -> dict[str, Device]:
        """Fetch data and periodic device discovery."""
        now = datetime.now()
        is_first_refresh = self.last_discovery is None
        discovery_interval_elapsed = (
            self.last_discovery is not None
            and now - self.last_discovery
            >= timedelta(minutes=DISCOVERY_INTERVAL_MINUTES)
        )

        if is_first_refresh or discovery_interval_elapsed:
            try:
                devices_list = await self.client.discover_devices()
            except WattsVisionAuthError as err:
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="authentication_failed",
                ) from err
            except (
                WattsVisionConnectionError,
                WattsVisionTimeoutError,
                WattsVisionDeviceError,
                WattsVisionError,
                ConnectionError,
                TimeoutError,
                ValueError,
            ) as err:
                if is_first_refresh:
                    raise ConfigEntryNotReady(
                        translation_domain=DOMAIN,
                        translation_key="failed_to_discover_devices",
                    ) from err
                _LOGGER.warning(
                    "Periodic discovery failed: %s, falling back to update", err
                )
            else:
                self.last_discovery = now
                devices = {device.device_id: device for device in devices_list}

                current_devices = set(devices.keys())
                if stale_devices := self.previous_devices - current_devices:
                    await self._remove_stale_devices(stale_devices)

                self.previous_devices = current_devices
                return devices

        # Regular update of existing devices
        device_ids = list(self.data.keys())
        if not device_ids:
            return {}

        try:
            devices = await self.client.get_devices_report(device_ids)
        except WattsVisionAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="authentication_failed",
            ) from err
        except (
            WattsVisionConnectionError,
            WattsVisionTimeoutError,
            WattsVisionDeviceError,
            WattsVisionError,
            ConnectionError,
            TimeoutError,
            ValueError,
        ) as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="failed_to_update_devices",
            ) from err

        _LOGGER.debug("Updated %d devices", len(devices))
        return devices