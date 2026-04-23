async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for the climate entity."""
        if preset_mode not in PRESET_MODE_MAP:
            _LOGGER.warning("Unknown preset mode: %s", preset_mode)
            return

        new_hvac_mode = self._attr_hvac_mode
        if preset_mode == "standby":
            new_hvac_mode = HVACMode.OFF
        elif self._attr_hvac_mode == HVACMode.OFF:
            new_hvac_mode = next(
                (
                    mode
                    for mode in (self._attr_hvac_modes or [])
                    if mode is not HVACMode.OFF
                ),
                HVACMode.HEAT,
            )

        ok = await self._set_device_mode(preset_mode)
        if not ok:
            raise HomeAssistantError(
                f"Failed to set preset mode '{preset_mode}' for {self.entity_id}"
            )

        self._attr_hvac_mode = new_hvac_mode
        if preset_mode != "standby":
            self._last_preset_mode = preset_mode
        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()