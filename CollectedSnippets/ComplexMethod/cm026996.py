async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self.unique_id}_poll_value",
                self.async_poll_value,
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self._base_unique_id}_remove_entity",
                self.async_remove,
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self._base_unique_id}_remove_entity_on_interview_started",
                self.async_remove,
            )
        )

        # Make sure these variables are set for the elif evaluation
        state = None
        latest_version = None

        # If we have a complete previous state, use that to set the latest version
        if (
            (state := await self.async_get_last_state())
            and (latest_version := state.attributes.get(ATTR_LATEST_VERSION))
            is not None
            and (extra_data := await self.async_get_last_extra_data())
            and (
                latest_version_firmware := ZWaveFirmwareUpdateExtraStoredData.from_dict(
                    extra_data.as_dict()
                ).latest_version_firmware
            )
        ):
            self._attr_latest_version = latest_version
            self._latest_version_firmware = latest_version_firmware
        # If we have no state or latest version to restore, or the latest version is
        # the same as the installed version, we can set the latest
        # version to installed so that the entity starts as off. If we have partial
        # restore data due to an upgrade to an HA version where this feature is released
        # from one that is not the entity will start in an unknown state until we can
        # correct on next update
        elif (
            not state
            or not latest_version
            or latest_version == self._attr_installed_version
        ):
            self._attr_latest_version = self._attr_installed_version

        # Spread updates out in 15 second increments
        # to avoid spamming the firmware server
        self.async_on_remove(
            async_call_later(self.hass, self._delay, self._async_update)
        )