async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if (
            preset_mode in (PRESET_BOOST, STATE_NETATMO_MAX)
            and self.device_type == NA_VALVE
            and self._attr_hvac_mode == HVACMode.HEAT
        ):
            await self.device.async_therm_set(
                STATE_NETATMO_HOME,
            )
        elif (
            preset_mode in (PRESET_BOOST, STATE_NETATMO_MAX)
            and self.device_type == NA_VALVE
        ):
            await self.device.async_therm_set(
                STATE_NETATMO_MANUAL,
                DEFAULT_MAX_TEMP,
            )
        elif (
            preset_mode in (PRESET_BOOST, STATE_NETATMO_MAX)
            and self._attr_hvac_mode == HVACMode.HEAT
        ):
            await self.device.async_therm_set(STATE_NETATMO_HOME)
        elif preset_mode in (PRESET_BOOST, STATE_NETATMO_MAX):
            await self.device.async_therm_set(PRESET_MAP_NETATMO[preset_mode])
        elif preset_mode in THERM_MODES:
            await self.device.home.async_set_thermmode(PRESET_MAP_NETATMO[preset_mode])
        else:
            _LOGGER.error("Preset mode '%s' not available", preset_mode)

        self.async_write_ha_state()