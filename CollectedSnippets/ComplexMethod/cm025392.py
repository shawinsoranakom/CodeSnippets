async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode for the climate entity."""
        if hvac_mode == HVACMode.OFF:
            if self._attr_preset_mode and self._attr_preset_mode != "standby":
                self._last_preset_mode = self._attr_preset_mode

            ok = await self._set_device_mode("standby")
            if not ok:
                raise HomeAssistantError(
                    f"Failed to set standby mode for {self.entity_id}"
                )
            self._attr_preset_mode = "standby"
        else:
            preset_to_restore = None
            if (
                self._last_preset_mode
                and self._attr_preset_modes is not None
                and self._last_preset_mode in self._attr_preset_modes
            ):
                preset_to_restore = self._last_preset_mode

            if not preset_to_restore:
                preset_to_restore = next(
                    (p for p in (self._attr_preset_modes or []) if p != "standby"),
                    "comfort",
                )

            ok = await self._set_device_mode(preset_to_restore)
            if not ok:
                raise HomeAssistantError(
                    f"Failed to restore preset '{preset_to_restore}' for {self.entity_id}"
                )
            self._attr_preset_mode = preset_to_restore

        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()