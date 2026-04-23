def _update_filter_sensor_state(
        self, new_state: State | None, update_ha: bool = True
    ) -> None:
        """Process device state changes."""
        if new_state is None:
            _LOGGER.warning(
                "While updating filter %s, the new_state is None", self.name
            )
            self._state = None
            self.async_write_ha_state()
            return

        if new_state.state == STATE_UNKNOWN:
            self._state = None
            self.async_write_ha_state()
            return

        if new_state.state == STATE_UNAVAILABLE:
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True

        temp_state = _State(new_state.last_updated, new_state.state)

        try:
            for filt in self._filters:
                filtered_state = filt.filter_state(copy(temp_state))
                _LOGGER.debug(
                    "%s(%s=%s) -> %s",
                    filt.name,
                    self._entity,
                    temp_state.state,
                    "skip" if filt.skip_processing else filtered_state.state,
                )
                if filt.skip_processing:
                    return
                temp_state = filtered_state
        except ValueError:
            _LOGGER.error(
                "Could not convert state: %s (%s) to number",
                new_state.state,
                type(new_state.state),
            )
            return

        self._state = temp_state.state

        self._attr_icon = new_state.attributes.get(ATTR_ICON, ICON)
        self._attr_device_class = new_state.attributes.get(ATTR_DEVICE_CLASS)
        self._attr_state_class = new_state.attributes.get(ATTR_STATE_CLASS)

        if self._attr_native_unit_of_measurement != new_state.attributes.get(
            ATTR_UNIT_OF_MEASUREMENT
        ):
            for filt in self._filters:
                filt.reset()
            self._attr_native_unit_of_measurement = new_state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT
            )

        if update_ha:
            self.async_write_ha_state()