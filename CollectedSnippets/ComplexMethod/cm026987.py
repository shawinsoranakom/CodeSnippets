async def _async_restore_network_backup(self) -> None:
        """Restore the backup."""
        assert self.backup_data is not None
        config_entry = self._reconfigure_config_entry
        assert config_entry is not None

        # Make sure we keep the old devices
        # so that user customizations are not lost,
        # when loading the config entry.
        self.hass.config_entries.async_update_entry(
            config_entry, data=config_entry.data | {CONF_KEEP_OLD_DEVICES: True}
        )

        # Reload the config entry to reconnect the client after the addon restart
        await self.hass.config_entries.async_reload(config_entry.entry_id)

        data = config_entry.data.copy()
        data.pop(CONF_KEEP_OLD_DEVICES, None)
        self.hass.config_entries.async_update_entry(config_entry, data=data)

        @callback
        def forward_progress(event: dict) -> None:
            """Forward progress events to frontend."""
            if event["event"] == "nvm convert progress":
                # assume convert is 50% of the total progress
                self.async_update_progress(event["bytesRead"] / event["total"] * 0.5)
            elif event["event"] == "nvm restore progress":
                # assume restore is the rest of the progress
                self.async_update_progress(
                    event["bytesWritten"] / event["total"] * 0.5 + 0.5
                )

        driver = self._get_driver()
        controller = driver.controller
        unsubs = [
            controller.on("nvm convert progress", forward_progress),
            controller.on("nvm restore progress", forward_progress),
        ]

        wait_for_driver_ready = async_wait_for_driver_ready_event(config_entry, driver)

        try:
            await controller.async_restore_nvm(
                self.backup_data, {"preserveRoutes": False}
            )
        except FailedCommand as err:
            raise AbortFlow(f"Failed to restore network: {err}") from err
        else:
            with suppress(TimeoutError):
                await wait_for_driver_ready()
            try:
                version_info = await async_get_version_info(
                    self.hass, config_entry.data[CONF_URL]
                )
            except CannotConnect:
                # Just log this error, as there's nothing to do about it here.
                # The stale unique id needs to be handled by a repair flow,
                # after the config entry has been reloaded.
                _LOGGER.error(
                    "Failed to get server version, cannot update config entry "
                    "unique id with new home id, after controller reset"
                )
            else:
                self.hass.config_entries.async_update_entry(
                    config_entry, unique_id=str(version_info.home_id)
                )

            # The config entry will be also be reloaded when the driver is ready,
            # by the listener in the package module,
            # and two reloads are needed to clean up the stale controller device entry.
            # Since both the old and the new controller have the same node id,
            # but different hardware identifiers, the integration
            # will create a new device for the new controller, on the first reload,
            # but not immediately remove the old device.
            await self.hass.config_entries.async_reload(config_entry.entry_id)

        finally:
            for unsub in unsubs:
                unsub()