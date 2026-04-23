def _get_current_preset_mode(self) -> str:
        """Return the current preset mode."""

        status = self._thermostat.status
        if status.is_window_open:
            return Preset.WINDOW_OPEN
        if status.is_boost:
            return Preset.BOOST
        if status.is_low_battery:
            return Preset.LOW_BATTERY
        if status.is_away:
            return Preset.AWAY
        if status.operation_mode is Eq3OperationMode.ON:
            return Preset.OPEN
        if status.presets is None:
            return PRESET_NONE
        if status.target_temperature == status.presets.eco_temperature:
            return Preset.ECO
        if status.target_temperature == status.presets.comfort_temperature:
            return Preset.COMFORT

        return PRESET_NONE