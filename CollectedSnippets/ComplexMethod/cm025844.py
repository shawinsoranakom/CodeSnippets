def _update_status(self) -> None:
        """Update status itself."""
        super()._update_status()

        self._attr_native_value = self.data.value

        # Update unit.
        if (
            unit_of_measurement := self._get_unit_of_measurement(self.data.unit)
        ) is not None:
            self._attr_native_unit_of_measurement = unit_of_measurement

        # Update range.
        if (
            self.entity_description.native_min_value is None
            and (min_value := self.data.min) is not None
        ):
            self._attr_native_min_value = min_value

        if (
            self.entity_description.native_max_value is None
            and (max_value := self.data.max) is not None
        ):
            self._attr_native_max_value = max_value

        if (
            self.entity_description.native_step is None
            and (step := self.data.step) is not None
        ):
            self._attr_native_step = step

        _LOGGER.debug(
            "[%s:%s] update status: %s -> %s, unit:%s, min:%s, max:%s, step:%s",
            self.coordinator.device_name,
            self.property_id,
            self.data.value,
            self.native_value,
            self.native_unit_of_measurement,
            self.native_min_value,
            self.native_max_value,
            self.native_step,
        )