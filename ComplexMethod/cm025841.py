def __init__(
        self,
        coordinator: DeviceDataUpdateCoordinator,
        entity_description: ClimateEntityDescription,
        property_id: str,
    ) -> None:
        """Initialize a climate entity."""
        super().__init__(coordinator, entity_description, property_id)

        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [HVACMode.OFF]
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_preset_modes = [PRESET_NONE]
        self._attr_preset_mode = PRESET_NONE
        self._attr_temperature_unit = (
            self._get_unit_of_measurement(self.data.unit) or UnitOfTemperature.CELSIUS
        )

        # Set up HVAC modes.
        for mode in self.data.hvac_modes:
            if mode in STR_TO_HVAC:
                self._attr_hvac_modes.append(STR_TO_HVAC[mode])
            elif mode in THINQ_PRESET_MODE:
                self._attr_preset_modes.append(mode)
                self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        # Set up fan modes.
        self._attr_fan_modes = [
            STR_TO_HA_FAN.get(fan, fan) for fan in self.data.fan_modes
        ]
        if self.fan_modes:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        # Supports target temperature range.
        if self.data.support_temperature_range:
            self._attr_supported_features |= (
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            )
        # Supports swing mode.
        if self.data.swing_modes:
            self._attr_swing_modes = [SWING_ON, SWING_OFF]
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        if self.data.swing_horizontal_modes:
            self._attr_swing_horizontal_modes = [SWING_ON, SWING_OFF]
            self._attr_supported_features |= ClimateEntityFeature.SWING_HORIZONTAL_MODE