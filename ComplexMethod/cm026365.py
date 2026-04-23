def _process_update(self) -> None:
        """Process an update from the coordinator."""
        state = self.coordinator.data
        if state is None or state.seconds_matched is None:
            self._attr_native_value = None
            return

        if self._type == CONF_TYPE_TIME:
            value = state.seconds_matched / 3600
            if self._attr_unique_id is None:
                value = round(value, 2)
            self._attr_native_value = value
        elif self._type == CONF_TYPE_RATIO:
            self._attr_native_value = pretty_ratio(state.seconds_matched, state.period)
        elif self._type == CONF_TYPE_COUNT:
            self._attr_native_value = state.match_count

        if self._preview_callback:
            calculated_state = self._async_calculate_state()
            self._preview_callback(
                None, calculated_state.state, calculated_state.attributes
            )