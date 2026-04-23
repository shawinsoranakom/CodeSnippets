async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperatures."""
        coordinator = self.coordinator
        hvac_mode = kwargs.get(ATTR_HVAC_MODE, self._attr_hvac_mode)

        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            if hvac_mode == HVACMode.HEAT:
                await coordinator.async_write_coil(
                    self._coil_setpoint_heat, temperature
                )
            elif hvac_mode == HVACMode.COOL:
                if self._coil_setpoint_cool:
                    await coordinator.async_write_coil(
                        self._coil_setpoint_cool, temperature
                    )
                else:
                    raise ServiceValidationError(
                        f"{hvac_mode} mode not supported for {self.name}"
                    )
            else:
                raise ServiceValidationError(
                    "'set_temperature' requires 'hvac_mode' when passing"
                    " 'temperature' and 'hvac_mode' is not already set to"
                    " 'heat' or 'cool'"
                )

        if (temperature := kwargs.get(ATTR_TARGET_TEMP_LOW)) is not None:
            await coordinator.async_write_coil(self._coil_setpoint_heat, temperature)

        if (
            self._coil_setpoint_cool
            and (temperature := kwargs.get(ATTR_TARGET_TEMP_HIGH)) is not None
        ):
            await coordinator.async_write_coil(self._coil_setpoint_cool, temperature)