def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        if self.has:
            new_value = self.entity_description.value_fn(self._value)
            if self.entity_description.key in CHARGE_ENERGY_RESET_KEYS and isinstance(
                new_value, float | int
            ):
                if self._previous_value is not None and (
                    (new_value == 0 and self._previous_value != 0)
                    or new_value < self._previous_value - CHARGE_ENERGY_RESET_THRESHOLD
                ):
                    self._attr_last_reset = dt_util.utcnow()
                self._previous_value = float(new_value)
            self._attr_native_value = new_value
        else:
            self._attr_native_value = None