async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all device and sensor data from api."""
        envoy = self.envoy
        for tries in range(2):
            try:
                if not self._setup_complete:
                    _LOGGER.debug("update on try %s, setup not complete", tries)
                    await self._async_setup_and_authenticate()
                    self._async_mark_setup_complete()
                # dump all received data in debug mode to assist troubleshooting
                envoy_data = await envoy.update()
            except INVALID_AUTH_ERRORS as err:
                _LOGGER.debug("update on try %s, INVALID_AUTH_ERRORS %s", tries, err)
                if self._setup_complete and tries == 0:
                    # token likely expired or firmware changed, try to re-authenticate
                    _LOGGER.debug("update on try %s, setup was complete, retry", tries)
                    self._setup_complete = False
                    continue
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="authentication_error",
                    translation_placeholders={
                        "host": envoy.host,
                        "args": err.args[0],
                    },
                ) from err
            except EnvoyError as err:
                _LOGGER.debug("update on try %s, EnvoyError %s", tries, err)
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="envoy_error",
                    translation_placeholders={
                        "host": envoy.host,
                        "args": err.args[0],
                    },
                ) from err

            # if we have a firmware version from previous setup, compare to current one
            # when envoy gets new firmware there will be an authentication failure
            # which results in getting fw version again, if so reload the integration.
            if (current_firmware := self.envoy_firmware) and current_firmware != (
                new_firmware := envoy.firmware
            ):
                _LOGGER.warning(
                    "Envoy firmware changed from: %s to: %s, reloading enphase envoy integration",
                    current_firmware,
                    new_firmware,
                )
                # reload the integration to get all established again
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.config_entry.entry_id)
                )
            # remember firmware version for next time
            self.envoy_firmware = envoy.firmware
            _LOGGER.debug("Envoy data: %s", envoy_data)
            return envoy_data.raw

        raise RuntimeError("Unreachable code in _async_update_data")