async def _async_update_data(self) -> None:
        """Update the host state cache and renew the ONVIF-subscription."""
        async with asyncio.timeout(self._update_timeout):
            try:
                await self._host.update_states()
            except CredentialsInvalidError as err:
                self._host.credential_errors += 1
                if self._host.credential_errors >= NUM_CRED_ERRORS:
                    await self._host.stop()
                    raise ConfigEntryAuthFailed(err) from err
                raise UpdateFailed(str(err)) from err
            except LoginPrivacyModeError:
                pass  # HTTP API is shutdown when privacy mode is active
            except ReolinkError as err:
                self._host.credential_errors = 0
                raise UpdateFailed(str(err)) from err

        self._host.credential_errors = 0

        # Check for firmware version changes (external update detection)
        firmware_changed = False
        for ch in (*self._host.api.channels, None):
            new_version = self._host.api.camera_sw_version(ch)
            old_version = self._last_known_firmware.get(ch)
            if (
                old_version is not None
                and new_version is not None
                and new_version != old_version
            ):
                firmware_changed = True
            self._last_known_firmware[ch] = new_version

        # Notify firmware coordinator if firmware changed externally
        if firmware_changed and self.firmware_coordinator is not None:
            self.firmware_coordinator.async_set_updated_data(None)

        async with asyncio.timeout(self._min_timeout):
            await self._host.renew()

        if (
            self._host.api.new_devices
            and self.config_entry.state == ConfigEntryState.LOADED
        ):
            # There are new cameras/chimes connected, reload to add them.
            _LOGGER.debug(
                "Reloading Reolink %s to add new device (capabilities)",
                self._host.api.nvr_name,
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.config_entry.entry_id)
            )