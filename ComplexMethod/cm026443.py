async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (
            (last_state := await self.async_get_last_state()) is not None
            and (extra_data := await self.async_get_last_binary_sensor_data())
            is not None
            and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
            # The trigger might have fired already while we waited for stored data,
            # then we should not restore state
            and self._attr_is_on is None
        ):
            self._attr_is_on = last_state.state == STATE_ON
            self.restore_attributes(last_state)

            if CONF_AUTO_OFF not in self._config:
                return

            if (
                auto_off_time := extra_data.auto_off_time
            ) is not None and auto_off_time <= dt_util.utcnow():
                # It's already past the saved auto off time
                self._attr_is_on = False

            if self._attr_is_on and auto_off_time is not None:
                self._set_auto_off(auto_off_time)