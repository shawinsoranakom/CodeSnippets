async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new temperature."""

        if self.is_using_derogated_temperature_fallback:
            await super().async_set_temperature(**kwargs)
            return

        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        target_temp_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        target_temp_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        hvac_mode = self.hvac_mode

        if hvac_mode == HVACMode.HEAT_COOL:
            if target_temp_low is not None:
                await self.executor.async_execute_command(
                    OverkizCommand.SET_HEATING_TARGET_TEMPERATURE,
                    target_temp_low,
                )

            if target_temp_high is not None:
                await self.executor.async_execute_command(
                    OverkizCommand.SET_COOLING_TARGET_TEMPERATURE,
                    target_temp_high,
                )

        elif target_temperature is not None:
            if hvac_mode == HVACMode.HEAT:
                await self.executor.async_execute_command(
                    OverkizCommand.SET_HEATING_TARGET_TEMPERATURE,
                    target_temperature,
                )

            elif hvac_mode == HVACMode.COOL:
                await self.executor.async_execute_command(
                    OverkizCommand.SET_COOLING_TARGET_TEMPERATURE,
                    target_temperature,
                )

        await self.executor.async_execute_command(
            OverkizCommand.SET_DEROGATION_ON_OFF_STATE,
            OverkizCommandParam.ON,
        )

        await self.async_refresh_modes()