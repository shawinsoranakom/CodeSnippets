def configuration(self) -> dict[str, Any] | None:
        """Return configuration object.

        Translates climate HVAC_MODES and PRESETS to supported Alexa
        ThermostatMode Values.

        ThermostatMode Value must be AUTO, COOL, HEAT, ECO, OFF, or CUSTOM.
        Water heater devices do not return thermostat modes.
        """
        if self.entity.domain == water_heater.DOMAIN:
            return None

        hvac_modes = self.entity.attributes.get(climate.ATTR_HVAC_MODES) or []
        supported_modes: list[str] = [
            API_THERMOSTAT_MODES[mode]
            for mode in hvac_modes
            if mode in API_THERMOSTAT_MODES
        ]

        preset_modes = self.entity.attributes.get(climate.ATTR_PRESET_MODES)
        if preset_modes:
            for mode in preset_modes:
                thermostat_mode = API_THERMOSTAT_PRESETS.get(mode)
                if thermostat_mode:
                    supported_modes.append(thermostat_mode)

        # Return False for supportsScheduling until supported with event
        # listener in handler.
        configuration: dict[str, Any] = {"supportsScheduling": False}

        if supported_modes:
            configuration["supportedModes"] = supported_modes

        return configuration