def __init__(
        self,
        coordinator: LyricDataUpdateCoordinator,
        description: ClimateEntityDescription,
        location: LyricLocation,
        device: LyricDevice,
    ) -> None:
        """Initialize Honeywell Lyric climate entity."""
        # Define thermostat type (TCC - e.g., Lyric round; LCC - e.g., T5,6)
        if device.changeable_values.thermostat_setpoint_status:
            self._attr_thermostat_type = LyricThermostatType.LCC
        else:
            self._attr_thermostat_type = LyricThermostatType.TCC

        # Use the native temperature unit from the device settings
        if device.units == "Fahrenheit":
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
            self._attr_precision = PRECISION_WHOLE
        else:
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
            self._attr_precision = PRECISION_HALVES

        # Setup supported hvac modes
        self._attr_hvac_modes = [HVACMode.OFF]

        # Add supported lyric thermostat features
        if LYRIC_HVAC_MODE_HEAT in device.allowed_modes:
            self._attr_hvac_modes.append(HVACMode.HEAT)

        if LYRIC_HVAC_MODE_COOL in device.allowed_modes:
            self._attr_hvac_modes.append(HVACMode.COOL)

        # TCC devices like the Lyric round do not have the Auto
        # option in allowed_modes, but still support Auto mode
        if LYRIC_HVAC_MODE_HEAT_COOL in device.allowed_modes or (
            self._attr_thermostat_type is LyricThermostatType.TCC
            and LYRIC_HVAC_MODE_HEAT in device.allowed_modes
            and LYRIC_HVAC_MODE_COOL in device.allowed_modes
        ):
            self._attr_hvac_modes.append(HVACMode.HEAT_COOL)

        # Setup supported features
        if self._attr_thermostat_type is LyricThermostatType.LCC:
            self._attr_supported_features = SUPPORT_FLAGS_LCC
        else:
            self._attr_supported_features = SUPPORT_FLAGS_TCC

        # Setup supported fan modes
        if device_fan_modes := device.settings.attributes.get("fan", {}).get(
            "allowedModes"
        ):
            self._attr_fan_modes = [
                FAN_MODES[device_fan_mode]
                for device_fan_mode in device_fan_modes
                if device_fan_mode in FAN_MODES
            ]
            self._attr_supported_features = (
                self._attr_supported_features | ClimateEntityFeature.FAN_MODE
            )

        if len(self.hvac_modes) > 1:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )

        super().__init__(
            coordinator,
            location,
            device,
            f"{device.mac_id}_thermostat",
        )
        self.entity_description = description