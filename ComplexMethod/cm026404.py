async def async_update(self) -> None:
        """Pull state from AEH-W4A1."""
        try:
            status = await self._device.command("status_102_0")
        except pyaehw4a1.exceptions.ConnectionError as library_error:
            _LOGGER.warning(
                "Unexpected error of %s: %s", self._attr_unique_id, library_error
            )
            self._attr_available = False
            return

        self._attr_available = True

        self._on = status["run_status"]

        if status["temperature_Fahrenheit"] == "0":
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
            self._attr_min_temp = MIN_TEMP_C
            self._attr_max_temp = MAX_TEMP_C
        else:
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
            self._attr_min_temp = MIN_TEMP_F
            self._attr_max_temp = MAX_TEMP_F

        self._attr_current_temperature = int(status["indoor_temperature_status"], 2)

        if self._on == "1":
            device_mode = status["mode_status"]
            self._attr_hvac_mode = AC_TO_HA_STATE[device_mode]

            fan_mode = status["wind_status"]
            self._attr_fan_mode = AC_TO_HA_FAN_MODES[fan_mode]

            swing_mode = f"{status['up_down']}{status['left_right']}"
            self._attr_swing_mode = AC_TO_HA_SWING[swing_mode]

            if self._attr_hvac_mode in (HVACMode.COOL, HVACMode.HEAT):
                self._attr_target_temperature = int(
                    status["indoor_temperature_setting"], 2
                )
            else:
                self._attr_target_temperature = None

            if status["efficient"] == "1":
                self._attr_preset_mode = PRESET_BOOST
            elif status["low_electricity"] == "1":
                self._attr_preset_mode = PRESET_ECO
            elif status["sleep_status"] == "0000001":
                self._attr_preset_mode = PRESET_SLEEP
            elif status["sleep_status"] == "0000010":
                self._attr_preset_mode = "sleep_2"
            elif status["sleep_status"] == "0000011":
                self._attr_preset_mode = "sleep_3"
            elif status["sleep_status"] == "0000100":
                self._attr_preset_mode = "sleep_4"
            else:
                self._attr_preset_mode = PRESET_NONE
        else:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_fan_mode = None
            self._attr_swing_mode = None
            self._attr_target_temperature = None
            self._attr_preset_mode = None