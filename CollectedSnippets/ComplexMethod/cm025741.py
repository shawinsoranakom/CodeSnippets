async def async_added_to_hass(self) -> None:
        """Register callback for ElkM1 changes."""
        await super().async_added_to_hass()
        if len(self._elk.areas.elements) == 1:
            for keypad in self._elk.keypads:
                keypad.add_callback(self._watch_keypad)
        self._element.add_callback(self._watch_area)

        # We do not get changed_by back from resync.
        if not (last_state := await self.async_get_last_state()):
            return

        if ATTR_CHANGED_BY_KEYPAD in last_state.attributes:
            self._changed_by_keypad = last_state.attributes[ATTR_CHANGED_BY_KEYPAD]
        if ATTR_CHANGED_BY_TIME in last_state.attributes:
            self._changed_by_time = last_state.attributes[ATTR_CHANGED_BY_TIME]
        if ATTR_CHANGED_BY_ID in last_state.attributes:
            self._changed_by_id = last_state.attributes[ATTR_CHANGED_BY_ID]
        if ATTR_CHANGED_BY in last_state.attributes:
            self._changed_by = last_state.attributes[ATTR_CHANGED_BY]