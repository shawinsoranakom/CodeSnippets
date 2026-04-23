def update(self) -> None:
        """Update the sensor."""
        try:
            sensor_type = self.entity_description.key
            if sensor_type == "movies":
                self._attr_native_value = self._ombi.movie_requests
            elif sensor_type == "tv":
                self._attr_native_value = self._ombi.tv_requests
            elif sensor_type == "music":
                self._attr_native_value = self._ombi.music_requests
            elif sensor_type == "pending":
                self._attr_native_value = self._ombi.total_requests["pending"]
            elif sensor_type == "approved":
                self._attr_native_value = self._ombi.total_requests["approved"]
            elif sensor_type == "available":
                self._attr_native_value = self._ombi.total_requests["available"]
        except OmbiError as err:
            _LOGGER.warning("Unable to update Ombi sensor: %s", err)
            self._attr_native_value = None