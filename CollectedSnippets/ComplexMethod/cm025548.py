async def async_update(self) -> None:
        """Update the device state and, if necessary, re-connect."""
        # Check if device is disconnected.
        if not self._attr_available:
            # Try to connect
            if await self.aftv.adb_connect(log_errors=self._failed_connect_count == 0):
                self._failed_connect_count = 0
                self._attr_available = True
            else:
                self._failed_connect_count += 1

        # If the ADB connection is not intact, don't update.
        if not self.available:
            return

        prev_app_id = self._attr_app_id
        # Get the updated state and attributes.
        (
            state,
            self._attr_app_id,
            running_apps,
            _,
            self._attr_is_volume_muted,
            self._attr_volume_level,
            self._attr_extra_state_attributes[ATTR_HDMI_INPUT],
        ) = await self.aftv.update(self._get_sources)

        self._attr_state = ANDROIDTV_STATES.get(state)
        if self._attr_state is None:
            self._attr_available = False

        if running_apps and self._attr_app_id:
            self._attr_source = self._attr_app_name = self._app_id_to_name.get(
                self._attr_app_id, self._attr_app_id
            )
            sources = [
                self._app_id_to_name.get(
                    app_id, app_id if not self._exclude_unnamed_apps else None
                )
                for app_id in running_apps
            ]
            self._attr_source_list = [source for source in sources if source]
        else:
            self._attr_source_list = None

        await self._async_get_screencap(prev_app_id)