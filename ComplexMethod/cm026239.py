async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        c4_climate = self._create_api_object()
        low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)
        high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temp = kwargs.get(ATTR_TEMPERATURE)

        # Handle temperature range for auto mode
        if self.hvac_mode == HVACMode.HEAT_COOL:
            if low_temp is not None:
                if self.temperature_unit == UnitOfTemperature.CELSIUS:
                    await c4_climate.setHeatSetpointC(low_temp)
                else:
                    await c4_climate.setHeatSetpointF(low_temp)
            if high_temp is not None:
                if self.temperature_unit == UnitOfTemperature.CELSIUS:
                    await c4_climate.setCoolSetpointC(high_temp)
                else:
                    await c4_climate.setCoolSetpointF(high_temp)
        # Handle single temperature setpoint
        elif temp is not None:
            if self.hvac_mode == HVACMode.COOL:
                if self.temperature_unit == UnitOfTemperature.CELSIUS:
                    await c4_climate.setCoolSetpointC(temp)
                else:
                    await c4_climate.setCoolSetpointF(temp)
            elif self.hvac_mode == HVACMode.HEAT:
                if self.temperature_unit == UnitOfTemperature.CELSIUS:
                    await c4_climate.setHeatSetpointC(temp)
                else:
                    await c4_climate.setHeatSetpointF(temp)

        await self.coordinator.async_request_refresh()