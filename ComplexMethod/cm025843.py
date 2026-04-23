async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            if hvac_mode == HVACMode.OFF:
                await self.async_turn_off()
                return

            if hvac_mode == HVACMode.HEAT_COOL:
                hvac_mode = HVACMode.AUTO

        # If device is off, turn on first.
        if not self.data.is_on:
            await self.async_turn_on()
            await asyncio.sleep(2)

        if hvac_mode and hvac_mode != self.hvac_mode:
            await self.async_set_hvac_mode(HVACMode(hvac_mode))
            await asyncio.sleep(2)
        _LOGGER.debug(
            "[%s:%s] async_set_temperature: %s",
            self.coordinator.device_name,
            self.property_id,
            kwargs,
        )
        if temperature := kwargs.get(ATTR_TEMPERATURE):
            if self.data.step >= 1:
                temperature = int(temperature)
            if temperature != self.target_temperature:
                await self.async_call_api(
                    self.coordinator.api.async_set_target_temperature(
                        self.property_id,
                        temperature,
                    )
                )

        if (temperature_low := kwargs.get(ATTR_TARGET_TEMP_LOW)) and (
            temperature_high := kwargs.get(ATTR_TARGET_TEMP_HIGH)
        ):
            if self.data.step >= 1:
                temperature_low = int(temperature_low)
                temperature_high = int(temperature_high)
            await self.async_call_api(
                self.coordinator.api.async_set_target_temperature_low_high(
                    self.property_id,
                    temperature_low,
                    temperature_high,
                )
            )