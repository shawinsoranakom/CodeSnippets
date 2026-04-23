async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_hvac_mode: HVACMode | None = kwargs.get(ATTR_HVAC_MODE)
        target_temperature: float | None = kwargs.get(ATTR_TEMPERATURE)
        target_temperature_low: float | None = kwargs.get(ATTR_TARGET_TEMP_LOW)
        target_temperature_high: float | None = kwargs.get(ATTR_TARGET_TEMP_HIGH)

        if target_hvac_mode is not None:
            await self.async_set_hvac_mode(target_hvac_mode)
        current_mode = target_hvac_mode or self.hvac_mode

        if target_temperature is not None:
            # single setpoint control
            if self.target_temperature != target_temperature:
                if current_mode == HVACMode.COOL:
                    matter_attribute = (
                        clusters.Thermostat.Attributes.OccupiedCoolingSetpoint
                    )
                else:
                    matter_attribute = (
                        clusters.Thermostat.Attributes.OccupiedHeatingSetpoint
                    )
                await self.write_attribute(
                    value=int(target_temperature * TEMPERATURE_SCALING_FACTOR),
                    matter_attribute=matter_attribute,
                )
            return

        if target_temperature_low is not None:
            # multi setpoint control - low setpoint (heat)
            if self.target_temperature_low != target_temperature_low:
                await self.write_attribute(
                    value=int(target_temperature_low * TEMPERATURE_SCALING_FACTOR),
                    matter_attribute=clusters.Thermostat.Attributes.OccupiedHeatingSetpoint,
                )

        if target_temperature_high is not None:
            # multi setpoint control - high setpoint (cool)
            if self.target_temperature_high != target_temperature_high:
                await self.write_attribute(
                    value=int(target_temperature_high * TEMPERATURE_SCALING_FACTOR),
                    matter_attribute=clusters.Thermostat.Attributes.OccupiedCoolingSetpoint,
                )