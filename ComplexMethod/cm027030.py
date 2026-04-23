def __init__(self, fibaro_device: DeviceModel) -> None:
        """Initialize the Fibaro device."""
        super().__init__(fibaro_device)
        self._temp_sensor_device: DeviceModel | None = None
        self._target_temp_device: DeviceModel | None = None
        self._op_mode_device: DeviceModel | None = None
        self._fan_mode_device: DeviceModel | None = None
        self.entity_id = ENTITY_ID_FORMAT.format(self.ha_id)

        siblings = self.controller.get_siblings(fibaro_device)
        _LOGGER.debug("%s siblings: %s", fibaro_device.ha_id, siblings)
        tempunit = "C"
        for device in siblings:
            # Detecting temperature device, one strong and one weak way of
            # doing so, so we prefer the hard evidence, if there is such.
            if device.type == "com.fibaro.temperatureSensor" or (
                self._temp_sensor_device is None
                and device.has_unit
                and (device.value.has_value or device.has_heating_thermostat_setpoint)
                and device.unit in ("C", "F")
            ):
                self._temp_sensor_device = device
                tempunit = device.unit

            if any(
                action for action in TARGET_TEMP_ACTIONS if action in device.actions
            ):
                self._target_temp_device = device
                self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
                if device.has_unit:
                    tempunit = device.unit

            if any(action for action in OP_MODE_ACTIONS if action in device.actions):
                self._op_mode_device = device
                self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

            if "setFanMode" in device.actions:
                self._fan_mode_device = device
                self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        if tempunit == "F":
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        else:
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS

        if self._fan_mode_device:
            fan_modes = self._fan_mode_device.supported_modes
            self._attr_fan_modes = []
            for mode in fan_modes:
                if mode not in FANMODES:
                    _LOGGER.warning("%d unknown fan mode", mode)
                    continue
                self._attr_fan_modes.append(FANMODES[int(mode)])

        self._attr_hvac_modes = [HVACMode.AUTO]  # default
        if self._op_mode_device:
            self._attr_preset_modes = []
            self._attr_hvac_modes: list[HVACMode] = []
            device = self._op_mode_device
            if device.has_supported_thermostat_modes:
                for mode in device.supported_thermostat_modes:
                    try:
                        self._attr_hvac_modes.append(HVACMode(mode.lower()))
                    except ValueError:
                        self._attr_preset_modes.append(mode)
            else:
                if device.has_supported_operating_modes:
                    op_modes = device.supported_operating_modes
                else:
                    op_modes = device.supported_modes
                for mode in op_modes:
                    if (
                        mode in OPMODES_HVAC
                        and (mode_ha := OPMODES_HVAC.get(mode))
                        and mode_ha not in self._attr_hvac_modes
                    ):
                        self._attr_hvac_modes.append(mode_ha)
                    if mode in OPMODES_PRESET:
                        self._attr_preset_modes.append(OPMODES_PRESET[mode])

        if HVACMode.OFF in self._attr_hvac_modes and len(self._attr_hvac_modes) > 1:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )