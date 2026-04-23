async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        new_heat_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)
        new_cool_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        set_temp = kwargs.get(ATTR_TEMPERATURE)

        deadband = self._thermostat.get_deadband()
        cur_cool_temp = self._zone.get_cooling_setpoint()
        cur_heat_temp = self._zone.get_heating_setpoint()
        (min_temp, max_temp) = self._thermostat.get_setpoint_limits()

        # Check that we're not going to hit any minimum or maximum values
        if new_heat_temp and new_heat_temp + deadband > max_temp:
            new_heat_temp = max_temp - deadband
        if new_cool_temp and new_cool_temp - deadband < min_temp:
            new_cool_temp = min_temp + deadband

        # Check that we're within the deadband range, fix it if we're not
        if (
            new_heat_temp
            and new_heat_temp != cur_heat_temp
            and new_cool_temp - new_heat_temp < deadband
        ):
            new_cool_temp = new_heat_temp + deadband

        if (
            new_cool_temp
            and new_cool_temp != cur_cool_temp
            and new_cool_temp - new_heat_temp < deadband
        ):
            new_heat_temp = new_cool_temp - deadband

        await self._zone.set_heat_cool_temp(
            heat_temperature=new_heat_temp,
            cool_temperature=new_cool_temp,
            set_temperature=set_temp,
        )
        self._signal_zone_update()