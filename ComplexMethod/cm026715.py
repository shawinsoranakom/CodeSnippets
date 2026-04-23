def _process_data(self) -> None:
        """Update and validate the data from the thermostat."""
        data = self.data.tstat
        if isinstance(self.device, radiotherm.thermostat.CT80):
            self._attr_current_humidity = self.data.humidity
            self._attr_preset_mode = CODE_TO_PRESET_MODE[data["program_mode"]]
        # Map thermostat values into various STATE_ flags.
        self._attr_current_temperature = data["temp"]
        self._attr_fan_mode = CODE_TO_FAN_MODE[data["fmode"]]
        self._attr_extra_state_attributes = {
            ATTR_FAN_ACTION: CODE_TO_FAN_STATE[data["fstate"]]
        }
        self._attr_hvac_mode = CODE_TO_TEMP_MODE[data["tmode"]]
        if self.hvac_mode == HVACMode.OFF:
            self._attr_hvac_action = None
        else:
            self._attr_hvac_action = CODE_TO_TEMP_STATE[data["tstate"]]
        if self.hvac_mode == HVACMode.COOL:
            self._attr_target_temperature = data["t_cool"]
        elif self.hvac_mode == HVACMode.HEAT:
            self._attr_target_temperature = data["t_heat"]
        elif self.hvac_mode == HVACMode.AUTO:
            # This doesn't really work - tstate is only set if the HVAC is
            # active. If it's idle, we don't know what to do with the target
            # temperature.
            if self.hvac_action == HVACAction.COOLING:
                self._attr_target_temperature = data["t_cool"]
            elif self.hvac_action == HVACAction.HEATING:
                self._attr_target_temperature = data["t_heat"]