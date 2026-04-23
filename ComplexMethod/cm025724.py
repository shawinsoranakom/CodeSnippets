async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if percentage is None and preset_mode is None:
            # turn_on without explicit percentage or preset_mode given
            # try to handle this with the last known value
            if self._last_known_percentage != 0:
                percentage = self._last_known_percentage
            elif self._last_known_preset_mode is not None:
                preset_mode = self._last_known_preset_mode
            elif self._attr_preset_modes:
                # fallback: default to first supported preset
                preset_mode = self._attr_preset_modes[0]
            else:
                # this really should not be possible but handle it anyways
                percentage = 50

        # prefer setting fan speed by percentage
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        # handle setting fan mode by preset
        if TYPE_CHECKING:
            assert preset_mode is not None
        await self.async_set_preset_mode(preset_mode)