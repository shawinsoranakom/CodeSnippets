async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        # Check before issuing the command in case targetValue report arrives early.
        already_closed = (
            (cv := self._current_position_value) is not None
            and cv.value is not None
            and (tpv := self._target_position_value) is not None
            and tpv.value == cv.value == self._fully_closed_position
        )
        result = await self._async_set_value(self._down_value, True)
        # StartLevelChange: SUCCESS means the device started moving in the desired direction
        if (
            result is not None
            and result.status in SET_VALUE_SUCCESS
            and self.supported_features & CoverEntityFeature.SET_POSITION
            and not already_closed
        ):
            self._attr_is_opening = False
            self._attr_is_closing = True
            self.async_write_ha_state()