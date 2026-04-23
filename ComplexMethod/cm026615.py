def __init__(
        self,
        device: CustomerDevice,
        device_manager: Manager,
        description: TuyaClimateEntityDescription,
        definition: TuyaClimateDefinition,
    ) -> None:
        """Determine which values to use."""
        super().__init__(device, device_manager, description)
        self._current_humidity_wrapper = definition.current_humidity_wrapper
        self._current_temperature = definition.current_temperature_wrapper
        self._fan_mode_wrapper = definition.fan_mode_wrapper
        self._hvac_mode_wrapper = definition.hvac_mode_wrapper
        self._preset_wrapper = definition.preset_wrapper
        self._set_temperature = definition.set_temperature_wrapper
        self._swing_wrapper = definition.swing_wrapper
        self._switch_wrapper = definition.switch_wrapper
        self._target_humidity_wrapper = definition.target_humidity_wrapper
        self._attr_temperature_unit = definition.temperature_unit

        # Get integer type data for the dpcode to set temperature, use
        # it to define min, max & step temperatures
        if definition.set_temperature_wrapper:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            self._attr_max_temp = definition.set_temperature_wrapper.max_value
            self._attr_min_temp = definition.set_temperature_wrapper.min_value
            self._attr_target_temperature_step = (
                definition.set_temperature_wrapper.value_step
            )

        # Determine HVAC modes
        self._attr_hvac_modes = []
        if definition.hvac_mode_wrapper:
            self._attr_hvac_modes = [HVACMode.OFF]
            for tuya_mode in cast(
                list[TuyaClimateHVACMode], definition.hvac_mode_wrapper.options
            ):
                if (
                    ha_mode := _TUYA_TO_HA_HVACMODE_MAPPINGS.get(tuya_mode)
                ) and ha_mode != HVACMode.OFF:
                    # OFF is always added first
                    self._attr_hvac_modes.append(ha_mode)

        elif definition.switch_wrapper:
            self._attr_hvac_modes = [
                HVACMode.OFF,
                description.switch_only_hvac_mode,
            ]

        # Determine preset modes (ignore if empty options)
        if definition.preset_wrapper and definition.preset_wrapper.options:
            self._attr_hvac_modes.append(description.switch_only_hvac_mode)
            self._attr_preset_modes = definition.preset_wrapper.options
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        # Determine dpcode to use for setting the humidity
        if definition.target_humidity_wrapper:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
            self._attr_min_humidity = round(
                definition.target_humidity_wrapper.min_value
            )
            self._attr_max_humidity = round(
                definition.target_humidity_wrapper.max_value
            )

        # Determine fan modes
        if definition.fan_mode_wrapper:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE
            self._attr_fan_modes = definition.fan_mode_wrapper.options

        # Determine swing modes
        if definition.swing_wrapper:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE
            self._attr_swing_modes = [
                ha_swing_mode
                for tuya_swing_mode in cast(
                    list[TuyaClimateSwingMode], definition.swing_wrapper.options
                )
                if (ha_swing_mode := _TUYA_TO_HA_SWING_MAPPINGS.get(tuya_swing_mode))
            ]

        if definition.switch_wrapper:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )