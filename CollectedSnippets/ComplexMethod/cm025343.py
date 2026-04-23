def _handle_coordinator_update(self) -> None:
        """Handle device update."""
        if not self.coordinator.device.initialized:
            self.async_write_ha_state()
            return

        if self.coordinator.device.status.get("calibrated") is False:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                NOT_CALIBRATED_ISSUE_ID.format(unique=self.coordinator.mac),
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="device_not_calibrated",
                translation_placeholders={
                    "device_name": self.coordinator.name,
                    "ip_address": self.coordinator.device.ip_address,
                },
            )
        else:
            ir.async_delete_issue(
                self.hass,
                DOMAIN,
                NOT_CALIBRATED_ISSUE_ID.format(unique=self.coordinator.mac),
            )

        assert self.coordinator.device.blocks

        for block in self.coordinator.device.blocks:
            if block.type == "device":
                self.device_block = block
            if hasattr(block, "targetTemp"):
                self.block = block

        if self.device_block and self.block:
            LOGGER.debug("Entity %s attached to blocks", self.name)

            assert self.block.channel

            try:
                self._preset_modes = [
                    PRESET_NONE,
                    *self.coordinator.device.settings["thermostats"][
                        int(self.block.channel)
                    ]["schedule_profile_names"],
                ]
            except InvalidAuthError:
                self.hass.async_create_task(
                    self.coordinator.async_shutdown_device_and_start_reauth(),
                    eager_start=True,
                )
            else:
                self.async_write_ha_state()