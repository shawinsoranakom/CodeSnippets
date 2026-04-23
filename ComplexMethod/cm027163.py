async def async_update(self) -> None:
        """Get the time and updates the states."""
        today = dt_util.now().date()
        state = moon.phase(today)

        if state < 0.5 or state > 27.5:
            self._attr_native_value = STATE_NEW_MOON
        elif state < 6.5:
            self._attr_native_value = STATE_WAXING_CRESCENT
        elif state < 7.5:
            self._attr_native_value = STATE_FIRST_QUARTER
        elif state < 13.5:
            self._attr_native_value = STATE_WAXING_GIBBOUS
        elif state < 14.5:
            self._attr_native_value = STATE_FULL_MOON
        elif state < 20.5:
            self._attr_native_value = STATE_WANING_GIBBOUS
        elif state < 21.5:
            self._attr_native_value = STATE_LAST_QUARTER
        else:
            self._attr_native_value = STATE_WANING_CRESCENT