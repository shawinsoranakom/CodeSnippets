async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature for the climate entity."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if self._attr_preset_mode != "setpoint":
            ok = await self._set_device_mode("setpoint")
            if not ok:
                raise HomeAssistantError(
                    f"Failed to set preset mode 'setpoint' for {self.entity_id}"
                )
            self._attr_preset_mode = "setpoint"
            if self._attr_hvac_mode == HVACMode.OFF:
                self._attr_hvac_mode = next(
                    (
                        mode
                        for mode in (self._attr_hvac_modes or [])
                        if mode is not HVACMode.OFF
                    ),
                    HVACMode.HEAT,
                )

        ok = await self._set_device_temperature(temperature)
        if not ok:
            raise HomeAssistantError(
                f"Failed to set temperature to {temperature} for {self.entity_id}"
            )

        self._attr_target_temperature = temperature
        self.async_write_ha_state()