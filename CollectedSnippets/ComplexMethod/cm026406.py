async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self._on != "1":
            if preset_mode == PRESET_NONE:
                return
            await self.async_turn_on()

        _LOGGER.debug(
            "Setting preset mode of %s to %s", self._attr_unique_id, preset_mode
        )

        if preset_mode == PRESET_ECO:
            await self._device.command("energysave_on")
            self._previous_state = preset_mode
        elif preset_mode == PRESET_BOOST:
            await self._device.command("turbo_on")
            self._previous_state = preset_mode
        elif preset_mode == PRESET_SLEEP:
            await self._device.command("sleep_1")
            self._previous_state = self._attr_hvac_mode
        elif preset_mode == "sleep_2":
            await self._device.command("sleep_2")
            self._previous_state = self._attr_hvac_mode
        elif preset_mode == "sleep_3":
            await self._device.command("sleep_3")
            self._previous_state = self._attr_hvac_mode
        elif preset_mode == "sleep_4":
            await self._device.command("sleep_4")
            self._previous_state = self._attr_hvac_mode
        elif self._previous_state is not None:
            if self._previous_state == PRESET_ECO:
                await self._device.command("energysave_off")
            elif self._previous_state == PRESET_BOOST:
                await self._device.command("turbo_off")
            elif self._previous_state in HA_STATE_TO_AC and isinstance(
                self._previous_state, HVACMode
            ):
                await self._device.command(HA_STATE_TO_AC[self._previous_state])
            self._previous_state = None