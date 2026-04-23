def __init__(
        self,
        hass: HomeAssistant,
        hub: ModbusHub,
        config: dict[str, Any],
    ) -> None:
        """Initialize the modbus thermostat."""
        super().__init__(hass, hub, config)
        self._target_temperature_register = config[CONF_TARGET_TEMP]
        self._target_temperature_write_registers = config[
            CONF_TARGET_TEMP_WRITE_REGISTERS
        ]
        self._unit = config[CONF_TEMPERATURE_UNIT]
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_temperature_unit = (
            UnitOfTemperature.FAHRENHEIT
            if self._unit == "F"
            else UnitOfTemperature.CELSIUS
        )
        self._attr_precision = (
            PRECISION_TENTHS if self._precision >= 1 else PRECISION_WHOLE
        )
        self._attr_min_temp = config[CONF_MIN_TEMP]
        self._attr_max_temp = config[CONF_MAX_TEMP]
        self._attr_target_temperature_step = config[CONF_STEP]
        self._current_temp_scale = config[CONF_CURRENT_TEMP_SCALE]
        self._current_temp_offset = config[CONF_CURRENT_TEMP_OFFSET]
        self._target_temp_scale = config[CONF_TARGET_TEMP_SCALE]
        self._target_temp_offset = config[CONF_TARGET_TEMP_OFFSET]

        if CONF_HVAC_MODE_REGISTER in config:
            mode_config = config[CONF_HVAC_MODE_REGISTER]
            self._hvac_mode_register = mode_config[CONF_ADDRESS]
            self._attr_hvac_modes = cast(list[HVACMode], [])
            self._attr_hvac_mode = None
            self._hvac_mode_mapping: list[tuple[int, HVACMode]] = []
            self._hvac_mode_write_registers = mode_config[CONF_WRITE_REGISTERS]
            mode_value_config = mode_config[CONF_HVAC_MODE_VALUES]

            for hvac_mode_kw, hvac_mode in (
                (CONF_HVAC_MODE_OFF, HVACMode.OFF),
                (CONF_HVAC_MODE_HEAT, HVACMode.HEAT),
                (CONF_HVAC_MODE_COOL, HVACMode.COOL),
                (CONF_HVAC_MODE_HEAT_COOL, HVACMode.HEAT_COOL),
                (CONF_HVAC_MODE_AUTO, HVACMode.AUTO),
                (CONF_HVAC_MODE_DRY, HVACMode.DRY),
                (CONF_HVAC_MODE_FAN_ONLY, HVACMode.FAN_ONLY),
            ):
                if hvac_mode_kw in mode_value_config:
                    values = mode_value_config[hvac_mode_kw]
                    if not isinstance(values, list):
                        values = [values]
                    for value in values:
                        self._hvac_mode_mapping.append((value, hvac_mode))
                    self._attr_hvac_modes.append(hvac_mode)
        else:
            # No HVAC modes defined
            self._hvac_mode_register = None
            self._attr_hvac_mode = HVACMode.AUTO
            self._attr_hvac_modes = [HVACMode.AUTO]

        if CONF_HVAC_ACTION_REGISTER in config:
            action_config = config[CONF_HVAC_ACTION_REGISTER]
            self._hvac_action_register = action_config[CONF_ADDRESS]
            self._hvac_action_type = action_config[CONF_INPUT_TYPE]

            self._attr_hvac_action = None
            self._hvac_action_mapping: list[tuple[int, HVACAction]] = []
            action_value_config = action_config[CONF_HVAC_ACTION_VALUES]

            for hvac_action_kw, hvac_action in (
                (CONF_HVAC_ACTION_COOLING, HVACAction.COOLING),
                (CONF_HVAC_ACTION_DEFROSTING, HVACAction.DEFROSTING),
                (CONF_HVAC_ACTION_DRYING, HVACAction.DRYING),
                (CONF_HVAC_ACTION_FAN, HVACAction.FAN),
                (CONF_HVAC_ACTION_HEATING, HVACAction.HEATING),
                (CONF_HVAC_ACTION_IDLE, HVACAction.IDLE),
                (CONF_HVAC_ACTION_OFF, HVACAction.OFF),
                (CONF_HVAC_ACTION_PREHEATING, HVACAction.PREHEATING),
            ):
                if hvac_action_kw in action_value_config:
                    values = action_value_config[hvac_action_kw]
                    if not isinstance(values, list):
                        values = [values]
                    for value in values:
                        self._hvac_action_mapping.append((value, hvac_action))
        else:
            self._hvac_action_register = None

        if CONF_FAN_MODE_REGISTER in config:
            self._attr_supported_features = (
                self._attr_supported_features | ClimateEntityFeature.FAN_MODE
            )
            mode_config = config[CONF_FAN_MODE_REGISTER]
            self._fan_mode_register = mode_config[CONF_ADDRESS]
            self._attr_fan_modes = cast(list[str], [])
            self._attr_fan_mode = None
            self._fan_mode_mapping_to_modbus: dict[str, int] = {}
            self._fan_mode_mapping_from_modbus: dict[int, str] = {}
            mode_value_config = mode_config[CONF_FAN_MODE_VALUES]
            for fan_mode_kw, fan_mode in (
                (CONF_FAN_MODE_ON, FAN_ON),
                (CONF_FAN_MODE_OFF, FAN_OFF),
                (CONF_FAN_MODE_AUTO, FAN_AUTO),
                (CONF_FAN_MODE_LOW, FAN_LOW),
                (CONF_FAN_MODE_MEDIUM, FAN_MEDIUM),
                (CONF_FAN_MODE_HIGH, FAN_HIGH),
                (CONF_FAN_MODE_TOP, FAN_TOP),
                (CONF_FAN_MODE_MIDDLE, FAN_MIDDLE),
                (CONF_FAN_MODE_FOCUS, FAN_FOCUS),
                (CONF_FAN_MODE_DIFFUSE, FAN_DIFFUSE),
            ):
                if fan_mode_kw in mode_value_config:
                    value = mode_value_config[fan_mode_kw]
                    self._fan_mode_mapping_from_modbus[value] = fan_mode
                    self._fan_mode_mapping_to_modbus[fan_mode] = value
                    self._attr_fan_modes.append(fan_mode)
        else:
            # No FAN modes defined
            self._fan_mode_register = None
            self._attr_fan_mode = FAN_AUTO
            self._attr_fan_modes = [FAN_AUTO]

        # No SWING modes defined
        self._swing_mode_register = None
        if CONF_SWING_MODE_REGISTER in config:
            self._attr_supported_features = (
                self._attr_supported_features | ClimateEntityFeature.SWING_MODE
            )
            mode_config = config[CONF_SWING_MODE_REGISTER]
            self._swing_mode_register = mode_config[CONF_ADDRESS]
            self._attr_swing_modes = cast(list[str], [])
            self._attr_swing_mode = None
            self._swing_mode_modbus_mapping: list[tuple[int, str]] = []
            mode_value_config = mode_config[CONF_SWING_MODE_VALUES]
            for swing_mode_kw, swing_mode in (
                (CONF_SWING_MODE_SWING_ON, SWING_ON),
                (CONF_SWING_MODE_SWING_OFF, SWING_OFF),
                (CONF_SWING_MODE_SWING_HORIZ, SWING_HORIZONTAL),
                (CONF_SWING_MODE_SWING_VERT, SWING_VERTICAL),
                (CONF_SWING_MODE_SWING_BOTH, SWING_BOTH),
            ):
                if swing_mode_kw in mode_value_config:
                    value = mode_value_config[swing_mode_kw]
                    self._swing_mode_modbus_mapping.append((value, swing_mode))
                    self._attr_swing_modes.append(swing_mode)

        if CONF_HVAC_ONOFF_REGISTER in config:
            self._hvac_onoff_register = config[CONF_HVAC_ONOFF_REGISTER]
            self._hvac_onoff_write_registers = config[CONF_WRITE_REGISTERS]
            self._hvac_on_value = config[CONF_HVAC_ON_VALUE]
            self._hvac_off_value = config[CONF_HVAC_OFF_VALUE]
            if HVACMode.OFF not in self._attr_hvac_modes:
                self._attr_hvac_modes.append(HVACMode.OFF)
        else:
            self._hvac_onoff_register = None

        if CONF_HVAC_ONOFF_COIL in config:
            self._hvac_onoff_coil = config[CONF_HVAC_ONOFF_COIL]
            if HVACMode.OFF not in self._attr_hvac_modes:
                self._attr_hvac_modes.append(HVACMode.OFF)
        else:
            self._hvac_onoff_coil = None