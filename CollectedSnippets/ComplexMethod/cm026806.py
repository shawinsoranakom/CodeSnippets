def async_update_state(self, new_state: State) -> None:
        """Update water_heater state after state change."""
        # Update current and target temperature
        target_temperature = _get_target_temperature(new_state, self._unit)
        if target_temperature is not None:
            self.char_target_temp.set_value(target_temperature)

        current_temperature = _get_current_temperature(new_state, self._unit)
        if current_temperature is not None:
            self.char_current_temp.set_value(current_temperature)

        # Update display units
        if self._unit and self._unit in UNIT_HASS_TO_HOMEKIT:
            unit = UNIT_HASS_TO_HOMEKIT[self._unit]
            self.char_display_units.set_value(unit)

        # Update target operation mode
        if new_state.state:
            if new_state.state == STATE_OFF and self._off_mode_available:
                self.char_target_heat_cool.set_value(HC_HEAT_COOL_OFF)
                self.char_current_heat_cool.set_value(HC_HEAT_COOL_OFF)
            else:
                self.char_target_heat_cool.set_value(HC_HEAT_COOL_HEAT)
                self.char_current_heat_cool.set_value(HC_HEAT_COOL_HEAT)