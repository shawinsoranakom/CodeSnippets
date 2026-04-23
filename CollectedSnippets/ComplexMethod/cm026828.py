def _set_chars(self, char_values: dict[str, Any]) -> None:
        _LOGGER.debug("Light _set_chars: %s", char_values)
        # Newest change always wins
        if CHAR_COLOR_TEMPERATURE in self._pending_events and (
            CHAR_SATURATION in char_values or CHAR_HUE in char_values
        ):
            del self._pending_events[CHAR_COLOR_TEMPERATURE]
        for char in (CHAR_HUE, CHAR_SATURATION):
            if char in self._pending_events and CHAR_COLOR_TEMPERATURE in char_values:
                del self._pending_events[char]

        self._pending_events.update(char_values)
        if self._event_timer:
            self._event_timer()
        self._event_timer = async_call_later(
            self.hass, CHANGE_COALESCE_TIME_WINDOW, self._async_send_events
        )