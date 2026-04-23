def _async_update_attrs(self) -> None:
        if self._device.temperature_unit == HeaterUnit.CELSIUS:
            self._attr_min_temp = 18
            self._attr_max_temp = 32
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        elif self._device.temperature_unit == HeaterUnit.FAHRENHEIT:
            self._attr_min_temp = 64
            self._attr_max_temp = 90
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT

        self._attr_current_temperature = self._device.current_temperature
        self._attr_target_temperature = self._device.target_temperature

        if self._device.is_heating:
            self._attr_hvac_action = HVACAction.HEATING
            self._attr_hvac_mode = HVACMode.AUTO
        elif self._device.is_active:
            self._attr_hvac_action = HVACAction.IDLE
            self._attr_hvac_mode = HVACMode.AUTO
        else:
            self._attr_hvac_action = HVACAction.OFF
            self._attr_hvac_mode = HVACMode.OFF

        match self._device.operation_mode:
            case HeaterMode.MANUAL:
                self._attr_preset_mode = PRESET_NONE
            case HeaterMode.BIO:
                self._attr_preset_mode = HEATER_BIO_MODE
            case HeaterMode.SMART:
                self._attr_preset_mode = HEATER_SMART_MODE