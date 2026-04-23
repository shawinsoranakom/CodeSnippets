async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if self.hvac_mode == HVACMode.OFF:
            return

        device = self.device
        target_temp_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        target_temp_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)

        if device.changeable_values.mode == LYRIC_HVAC_MODE_HEAT_COOL:
            if target_temp_low is None or target_temp_high is None:
                raise HomeAssistantError(
                    "Could not find target_temp_low and/or target_temp_high in"
                    " arguments"
                )

            # If TCC device pass the heatCoolMode value, otherwise
            # if LCC device can skip the mode altogether
            if self._attr_thermostat_type is LyricThermostatType.TCC:
                mode = HVAC_MODES[device.changeable_values.heat_cool_mode]
            else:
                mode = None

            _LOGGER.debug("Set temperature: %s - %s", target_temp_low, target_temp_high)
            try:
                await self._update_thermostat(
                    self.location,
                    device,
                    cool_setpoint=target_temp_high,
                    heat_setpoint=target_temp_low,
                    mode=mode,
                )
            except LYRIC_EXCEPTIONS as exception:
                _LOGGER.error(exception)
            await self.coordinator.async_refresh()
        else:
            temp = kwargs.get(ATTR_TEMPERATURE)
            _LOGGER.debug("Set temperature: %s", temp)
            try:
                if self.hvac_mode == HVACMode.COOL:
                    await self._update_thermostat(
                        self.location, device, cool_setpoint=temp
                    )
                else:
                    await self._update_thermostat(
                        self.location, device, heat_setpoint=temp
                    )
            except LYRIC_EXCEPTIONS as exception:
                _LOGGER.error(exception)
            await self.coordinator.async_refresh()