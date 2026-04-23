async def _async_set_position_and_update_moving_state(
        self, target_position: int
    ) -> None:
        """Set the target position and update the moving state if applicable."""
        assert self._target_position_value
        result = await self._async_set_value(
            self._target_position_value, target_position
        )
        if (
            self._moving_state_disabled
            # If the command is unsupervised, or the device reported that it started
            # working, we can assume the cover is moving in the desired direction.
            or result is None
            or result.status
            not in (SetValueStatus.WORKING, SetValueStatus.SUCCESS_UNSUPERVISED)
            # If we don't know the current position, we don't know which direction
            # the cover is moving, so we can't update the moving state.
            or (current_value := self._current_position_value) is None
            or (current := current_value.value) is None
        ):
            return

        if target_position > current:
            self._attr_is_opening = True
            self._attr_is_closing = False
        elif target_position < current:
            self._attr_is_opening = False
            self._attr_is_closing = True
        else:
            return

        self.async_write_ha_state()