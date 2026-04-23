def on_value_update(self) -> None:
        """Clear moving state when current position reaches target."""
        if not self._attr_is_opening and not self._attr_is_closing:
            return

        if (current := self._current_position_value) is None or current.value is None:
            return

        if (
            (t := self._target_position_value) is not None
            and t.value is not None
            and current.value == t.value
        ):
            self._attr_is_opening = False
            self._attr_is_closing = False