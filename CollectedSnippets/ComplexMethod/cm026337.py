def _get_current_action(self) -> HVACAction:
        if self._thermostat.current_temp is None:
            return HVACAction.OFF
        if (
            self._thermostat.temp_target_min is not None
            and self._thermostat.current_temp < self._thermostat.temp_target_min
            and self._thermostat.enabled_below_output
        ):
            return HVACAction.HEATING
        if (
            self._thermostat.temp_target_max is not None
            and self._thermostat.current_temp > self._thermostat.temp_target_max
            and self._thermostat.enabled_above_output
        ):
            return HVACAction.COOLING
        if (
            self._thermostat.temp_target_min is not None
            and self._thermostat.temp_target_max is not None
            and self._thermostat.current_temp >= self._thermostat.temp_target_min
            and self._thermostat.current_temp <= self._thermostat.temp_target_max
            and self._thermostat.enabled_inrange_output
        ):
            return HVACAction.FAN
        return HVACAction.IDLE