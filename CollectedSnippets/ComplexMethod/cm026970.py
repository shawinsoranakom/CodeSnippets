async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        # Check before issuing the command in case targetValue report arrives early.
        already_open = (
            (cv := self._current_position_value) is not None
            and cv.value is not None
            and (tpv := self._target_position_value) is not None
            and tpv.value == cv.value == self._fully_open_position
        )
        result = await self._async_set_value(self._up_value, True)
        # StartLevelChange: SUCCESS means the device started moving in the desired direction
        if (
            result is not None
            and result.status in SET_VALUE_SUCCESS
            and self.supported_features & CoverEntityFeature.SET_POSITION
            and not already_open
        ):
            self._attr_is_opening = True
            self._attr_is_closing = False
            self.async_write_ha_state()