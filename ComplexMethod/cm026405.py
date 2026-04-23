async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        if self._on != "1":
            _LOGGER.warning(
                "AC at %s is off, could not set swing mode", self._attr_unique_id
            )
            return

        _LOGGER.debug(
            "Setting swing mode of %s to %s", self._attr_unique_id, swing_mode
        )
        swing_act = self._attr_swing_mode

        if swing_mode == SWING_OFF and swing_act != SWING_OFF:
            if swing_act in (SWING_HORIZONTAL, SWING_BOTH):
                await self._device.command("hor_dir")
            if swing_act in (SWING_VERTICAL, SWING_BOTH):
                await self._device.command("vert_dir")

        if swing_mode == SWING_BOTH and swing_act != SWING_BOTH:
            if swing_act in (SWING_OFF, SWING_HORIZONTAL):
                await self._device.command("vert_swing")
            if swing_act in (SWING_OFF, SWING_VERTICAL):
                await self._device.command("hor_swing")

        if swing_mode == SWING_VERTICAL and swing_act != SWING_VERTICAL:
            if swing_act in (SWING_OFF, SWING_HORIZONTAL):
                await self._device.command("vert_swing")
            if swing_act in (SWING_BOTH, SWING_HORIZONTAL):
                await self._device.command("hor_dir")

        if swing_mode == SWING_HORIZONTAL and swing_act != SWING_HORIZONTAL:
            if swing_act in (SWING_BOTH, SWING_VERTICAL):
                await self._device.command("vert_dir")
            if swing_act in (SWING_OFF, SWING_VERTICAL):
                await self._device.command("hor_swing")