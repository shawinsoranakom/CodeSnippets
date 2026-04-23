def __init__(
        self,
        unique_id: str,
        device_name: str,
        target_temperature: float | None,
        unit_of_measurement: str,
        preset: str | None,
        current_temperature: float,
        fan_mode: str | None,
        target_humidity: float | None,
        current_humidity: float | None,
        swing_mode: str | None,
        swing_horizontal_mode: str | None,
        hvac_mode: HVACMode,
        hvac_action: HVACAction | None,
        target_temp_high: float | None,
        target_temp_low: float | None,
        hvac_modes: list[HVACMode],
        preset_modes: list[str] | None = None,
        target_humidity_step: int | None = None,
    ) -> None:
        """Initialize the climate device."""
        self._unique_id = unique_id
        self._attr_supported_features = SUPPORT_FLAGS
        if target_temperature is not None:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if preset is not None:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        if fan_mode is not None:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE
        if target_humidity is not None:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
        if swing_mode is not None:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE
        if swing_horizontal_mode is not None:
            self._attr_supported_features |= ClimateEntityFeature.SWING_HORIZONTAL_MODE
        if HVACMode.HEAT_COOL in hvac_modes or HVACMode.AUTO in hvac_modes:
            self._attr_supported_features |= (
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            )
        self._attr_supported_features |= (
            ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        )
        self._target_temperature = target_temperature
        self._target_humidity = target_humidity
        self._unit_of_measurement = unit_of_measurement
        self._preset = preset
        self._preset_modes = preset_modes
        self._current_temperature = current_temperature
        self._current_humidity = current_humidity
        self._current_fan_mode = fan_mode
        self._hvac_action = hvac_action
        self._hvac_mode = hvac_mode
        self._current_swing_mode = swing_mode
        self._current_swing_horizontal_mode = swing_horizontal_mode
        self._fan_modes = ["on_low", "on_high", "auto_low", "auto_high", "off"]
        self._hvac_modes = hvac_modes
        self._swing_modes = ["auto", "1", "2", "3", "off"]
        self._swing_horizontal_modes = ["auto", "rangefull", "off"]
        self._target_temperature_high = target_temp_high
        self._target_temperature_low = target_temp_low
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=device_name,
        )
        self._attr_target_humidity_step = target_humidity_step