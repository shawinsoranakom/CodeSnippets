def async_update_callback(self) -> None:
        """Update the entity's state."""
        data = self.entity_description.value_fn(self._station)

        if not data:
            if self.available:
                _LOGGER.error(
                    "No station provides %s data in the area %s",
                    self.entity_description.key,
                    self.area.area_name,
                )

            self._attr_available = False
            return

        if values := [x for x in data.values() if x is not None]:
            if self._mode == "avg":
                self._attr_native_value = round(sum(values) / len(values), 1)
            elif self._mode == "max":
                self._attr_native_value = max(values)
            elif self._mode == "min":
                self._attr_native_value = min(values)

        self._attr_available = self.native_value is not None
        self.async_write_ha_state()