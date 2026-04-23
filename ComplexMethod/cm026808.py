def _async_update_filter_life_level(self, new_state: State | None) -> None:
        """Handle linked filter life level sensor state change to update HomeKit value."""
        if new_state is None or new_state.state in IGNORED_STATES:
            return

        if (
            (current_life_level := convert_to_float(new_state.state)) is not None
            and self.char_filter_life_level
            and self.char_filter_life_level.value != current_life_level
        ):
            _LOGGER.debug(
                "%s: Linked filter life level sensor %s changed to %d",
                self.entity_id,
                self.linked_filter_life_level_sensor,
                current_life_level,
            )
            self.char_filter_life_level.set_value(current_life_level)

        if self.linked_filter_change_indicator_binary_sensor or not current_life_level:
            # Handled by its own event listener
            return

        current_change_indicator = (
            FILTER_CHANGE_FILTER
            if (current_life_level < THRESHOLD_FILTER_CHANGE_NEEDED)
            else FILTER_OK
        )
        if (
            not self.char_filter_change_indication
            or self.char_filter_change_indication.value == current_change_indicator
        ):
            return

        _LOGGER.debug(
            "%s: Linked filter life level sensor %s changed to %d",
            self.entity_id,
            self.linked_filter_life_level_sensor,
            current_change_indicator,
        )
        self.char_filter_change_indication.set_value(current_change_indicator)