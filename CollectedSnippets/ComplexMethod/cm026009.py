async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        hvac_mode = self.hvac_mode
        if kwargs.get(ATTR_HVAC_MODE) is not None:
            hvac_mode = kwargs[ATTR_HVAC_MODE]
            await self.async_set_hvac_mode(hvac_mode)
        low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)
        high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temp = kwargs.get(ATTR_TEMPERATURE)
        if ThermostatTemperatureSetpointTrait.NAME not in self._device.traits:
            raise HomeAssistantError(
                f"Error setting {self.entity_id} temperature to {kwargs}: "
                "Unable to find setpoint trait."
            )
        trait = self._device.traits[ThermostatTemperatureSetpointTrait.NAME]
        try:
            if self.preset_mode == PRESET_ECO or hvac_mode == HVACMode.HEAT_COOL:
                if low_temp and high_temp:
                    if high_temp - low_temp < MIN_TEMP_RANGE:
                        # Ensure there is a minimum gap from the new temp. Pick
                        # the temp that is not changing as the one to move.
                        if abs(high_temp - self.target_temperature_high) < 0.01:
                            high_temp = low_temp + MIN_TEMP_RANGE
                        else:
                            low_temp = high_temp - MIN_TEMP_RANGE
                    await trait.set_range(low_temp, high_temp)
            elif hvac_mode == HVACMode.COOL and temp:
                await trait.set_cool(temp)
            elif hvac_mode == HVACMode.HEAT and temp:
                await trait.set_heat(temp)
        except ApiException as err:
            raise HomeAssistantError(
                f"Error setting {self.entity_id} temperature to {kwargs}: {err}"
            ) from err