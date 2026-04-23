def _init_from_device_config(
        self,
        device: XknxClimate,
        default_hvac_mode: HVACMode,
        fan_max_step: int,
        fan_zero_mode: str,
    ) -> None:
        """Set attributes that depend on device config."""
        self.default_hvac_mode = default_hvac_mode
        # non-OFF HVAC mode to be used when turning on the device without on_off address
        self._last_hvac_mode = self.default_hvac_mode

        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        if device.supports_on_off:
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )
        if (
            device.mode is not None
            and len(device.mode.controller_modes) >= 2
            and HVACControllerMode.OFF in device.mode.controller_modes
        ):
            self._attr_supported_features |= (
                ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
            )

        if (
            device.mode is not None
            and device.mode.operation_modes  # empty list when not writable
        ):
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = [
                mode.name.lower() for mode in device.mode.operation_modes
            ]

        self.fan_zero_mode = fan_zero_mode
        self._fan_modes_percentages = [
            int(100 * i / fan_max_step) for i in range(fan_max_step + 1)
        ]
        if device.fan_speed is not None and device.fan_speed.initialized:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

            if fan_max_step == 3:
                self._attr_fan_modes = [
                    fan_zero_mode,
                    FAN_LOW,
                    FAN_MEDIUM,
                    FAN_HIGH,
                ]
            elif fan_max_step == 2:
                self._attr_fan_modes = [fan_zero_mode, FAN_LOW, FAN_HIGH]
            elif fan_max_step == 1:
                self._attr_fan_modes = [fan_zero_mode, FAN_ON]
            elif device.fan_speed_mode == FanSpeedMode.STEP:
                self._attr_fan_modes = [fan_zero_mode] + [
                    str(i) for i in range(1, fan_max_step + 1)
                ]
            else:
                self._attr_fan_modes = [fan_zero_mode] + [
                    f"{percentage}%" for percentage in self._fan_modes_percentages[1:]
                ]

        if device.swing.initialized:
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE
            self._attr_swing_modes = [SWING_ON, SWING_OFF]

        if device.horizontal_swing.initialized:
            self._attr_supported_features |= ClimateEntityFeature.SWING_HORIZONTAL_MODE
            self._attr_swing_horizontal_modes = [SWING_ON, SWING_OFF]

        self._attr_target_temperature_step = device.temperature_step