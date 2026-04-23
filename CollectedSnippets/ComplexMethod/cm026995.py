async def _async_update(self, _: HomeAssistant | datetime | None = None) -> None:
        """Update the entity."""
        if self._poll_unsub:
            self._poll_unsub()
            self._poll_unsub = None

        # If hass hasn't started yet, push the next update to the next day so that we
        # can preserve the offsets we've created between each node
        if self.hass.state is not CoreState.running:
            self._poll_unsub = async_call_later(
                self.hass, timedelta(days=1), self._async_update
            )
            return

        try:
            # Retrieve all firmware updates including non-stable ones but filter
            # non-stable channels out
            available_firmware_updates = [
                update
                for update in await self.driver.controller.async_get_available_firmware_updates(
                    self.node, API_KEY_FIRMWARE_UPDATE_SERVICE, True
                )
                if update.channel == "stable"
            ]
        except FailedZWaveCommand as err:
            LOGGER.debug(
                "Failed to get firmware updates for node %s: %s",
                self.node.node_id,
                err,
            )
        else:
            # If we have an available firmware update that is a higher version than
            # what's on the node, we should advertise it, otherwise the installed
            # version is the latest.
            if (
                available_firmware_updates
                and (
                    latest_firmware := max(
                        available_firmware_updates,
                        key=lambda x: AwesomeVersion(x.version),
                    )
                )
                and AwesomeVersion(latest_firmware.version)
                > AwesomeVersion(self.node.firmware_version)
            ):
                self._latest_version_firmware = latest_firmware
                self._attr_latest_version = latest_firmware.version
                self.async_write_ha_state()
            elif self._attr_latest_version != self._attr_installed_version:
                self._attr_latest_version = self._attr_installed_version
                self.async_write_ha_state()
        finally:
            self._poll_unsub = async_call_later(
                self.hass, timedelta(days=1), self._async_update
            )