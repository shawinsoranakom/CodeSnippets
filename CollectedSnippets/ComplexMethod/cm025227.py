async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if value := kwargs.get(ATTR_TARGET_TEMP_HIGH):
            temp = int(value)
            if not await self._client.set_cooling_setpoint(temp):
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="failed_to_set_clsp"
                )
            self._attr_target_temperature_high = temp

        if value := kwargs.get(ATTR_TARGET_TEMP_LOW):
            temp = int(value)
            if not await self._client.set_heating_setpoint(temp):
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="failed_to_set_htsp"
                )
            self._attr_target_temperature_low = temp

        if value := kwargs.get(ATTR_TEMPERATURE):
            temp = int(value)
            fn = (
                self._client.set_heating_setpoint
                if self.hvac_mode == HVACMode.HEAT
                else self._client.set_cooling_setpoint
            )
            if not await fn(temp):
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="failed_to_set_temp"
                )
            self._attr_target_temperature = temp

        # If we get here, we must have changed something unless HA allowed an
        # invalid service call (without any recognized kwarg).
        self._async_write_ha_state()