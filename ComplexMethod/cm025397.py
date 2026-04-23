async def _async_update_data(self) -> DeviceState | None:
        """Update data via library."""
        await self._verify_api()
        try:
            # Update device props and standard api information
            await self._update_device_prop()
        except UpdateFailed:
            if self._should_suppress_update_failure():
                _LOGGER.debug(
                    "Suppressing update failure until unavailable duration passed"
                )
                return self.data
            raise

        # If the vacuum is currently cleaning and it has been IMAGE_CACHE_INTERVAL
        # since the last map update, you can update the map.
        new_status = self.properties_api.status
        if (
            new_status.in_cleaning
            and (dt_util.utcnow() - self._last_home_update_attempt)
            > IMAGE_CACHE_INTERVAL
        ) or self.last_update_state != new_status.state_name:
            self._last_home_update_attempt = dt_util.utcnow()
            try:
                await self.update_map()
            except HomeAssistantError as err:
                _LOGGER.debug("Failed to update map: %s", err)

        if self.properties_api.status.in_cleaning:
            if self._device.is_local_connected:
                self.update_interval = V1_LOCAL_IN_CLEANING_INTERVAL
            else:
                self.update_interval = V1_CLOUD_IN_CLEANING_INTERVAL
        elif self._device.is_local_connected:
            self.update_interval = V1_LOCAL_NOT_CLEANING_INTERVAL
        else:
            self.update_interval = V1_CLOUD_NOT_CLEANING_INTERVAL
        self.last_update_state = self.properties_api.status.state_name
        self._last_update_success_time = dt_util.utcnow()
        _LOGGER.debug("Data update successful %s", self._last_update_success_time)
        return DeviceState(
            status=self.properties_api.status,
            dnd_timer=self.properties_api.dnd,
            consumable=self.properties_api.consumables,
            clean_summary=self.properties_api.clean_summary,
        )