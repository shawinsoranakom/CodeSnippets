async def _async_set_brightness(
        self, brightness: int | None, transition: float | None = None
    ) -> None:
        """Set new brightness to light."""
        # If we have no target brightness value, there is nothing to do
        if not self._target_brightness:
            return
        if brightness is None:
            zwave_brightness = SET_TO_PREVIOUS_VALUE
        else:
            # Zwave multilevel switches use a range of [0, 99] to control brightness.
            zwave_brightness = byte_to_zwave_brightness(brightness)

        # set transition value before sending new brightness
        zwave_transition = None
        if self.supports_brightness_transition:
            if transition is not None:
                zwave_transition = {TRANSITION_DURATION_OPTION: f"{int(transition)}s"}
            else:
                zwave_transition = {TRANSITION_DURATION_OPTION: "default"}

        # setting a value requires setting targetValue
        if self._supports_dimming:
            await self._async_set_value(
                self._target_brightness, zwave_brightness, zwave_transition
            )
        else:
            await self._async_set_value(
                self._target_brightness, zwave_brightness > 0, zwave_transition
            )
        # We do an optimistic state update when setting to a previous value
        # to avoid waiting for the value to be updated from the device which is
        # typically delayed and causes a confusing UX.
        if (
            zwave_brightness == SET_TO_PREVIOUS_VALUE
            and self.info.primary_value.command_class
            in (CommandClass.BASIC, CommandClass.SWITCH_MULTILEVEL)
        ):
            self._set_optimistic_state = True
            self.async_write_ha_state()