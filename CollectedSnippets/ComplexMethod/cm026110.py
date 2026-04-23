async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of device."""
        if preset_mode not in self._available_preset_modes:
            raise ValueError(
                f"{preset_mode} is not one of the valid preset modes: "
                f"{self._available_preset_modes}"
            )

        if not self.device.is_on:
            await self.device.turn_on()

        vs_mode = self._ha_to_vs_mode_map.get(preset_mode)
        success = False
        if vs_mode == VS_FAN_MODE_AUTO:
            success = await self.device.set_auto_mode()
        elif vs_mode == VS_FAN_MODE_SLEEP:
            success = await self.device.set_sleep_mode()
        elif vs_mode == VS_FAN_MODE_PET:
            if hasattr(self.device, "set_pet_mode"):
                success = await self.device.set_pet_mode()
        elif vs_mode == VS_FAN_MODE_TURBO:
            success = await self.device.set_turbo_mode()
        elif vs_mode == VS_FAN_MODE_NORMAL:
            if hasattr(self.device, "set_normal_mode"):
                success = await self.device.set_normal_mode()

        if not success:
            if self.device.last_response:
                raise HomeAssistantError(self.device.last_response.message)
            raise HomeAssistantError("Failed to set preset mode, no response found.")

        self.async_write_ha_state()