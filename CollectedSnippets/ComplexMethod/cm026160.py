def _get_current_temperature(self) -> float | None:
        """Return the current temperature."""

        match self._eq3_config.current_temp_selector:
            case CurrentTemperatureSelector.NOTHING:
                return None
            case CurrentTemperatureSelector.VALVE:
                return float(self._thermostat.status.valve_temperature)
            case CurrentTemperatureSelector.UI:
                return self._target_temperature
            case CurrentTemperatureSelector.DEVICE:
                return float(self._thermostat.status.target_temperature)
            case CurrentTemperatureSelector.ENTITY:
                state = self.hass.states.get(self._eq3_config.external_temp_sensor)
                if state is not None:
                    try:
                        return float(state.state)
                    except ValueError:
                        pass

        return None