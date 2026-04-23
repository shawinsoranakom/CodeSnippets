def _handle_coordinator_update(self) -> None:
        def _get_value(coil: Coil) -> int | str | float | date | None:
            return self.coordinator.get_coil_value(coil)

        def _get_float(coil: Coil) -> float | None:
            return self.coordinator.get_coil_float(coil)

        self._attr_current_temperature = _get_float(self._coil_current)

        mode = HVACMode.AUTO
        if _get_value(self._coil_use_room_sensor) == "ON":
            if (
                _get_value(self._coil_cooling_with_room_sensor)
                in VALUES_COOL_WITH_ROOM_SENSOR_OFF
            ):
                mode = HVACMode.HEAT
            else:
                mode = HVACMode.HEAT_COOL
        self._attr_hvac_mode = mode

        setpoint_heat = _get_float(self._coil_setpoint_heat)
        if self._coil_setpoint_cool:
            setpoint_cool = _get_float(self._coil_setpoint_cool)
        else:
            setpoint_cool = None
        if mode == HVACMode.HEAT_COOL:
            self._attr_target_temperature = None
            self._attr_target_temperature_low = setpoint_heat
            self._attr_target_temperature_high = setpoint_cool
        elif mode == HVACMode.HEAT:
            self._attr_target_temperature = setpoint_heat
            self._attr_target_temperature_low = None
            self._attr_target_temperature_high = None
        else:
            self._attr_target_temperature = None
            self._attr_target_temperature_low = None
            self._attr_target_temperature_high = None

        if prio := _get_value(self._coil_prio):
            if (
                _get_value(self._coil_mixing_valve_state)
                in VALUES_MIXING_VALVE_CLOSED_STATE
            ):
                self._attr_hvac_action = HVACAction.IDLE
            elif prio in VALUES_PRIORITY_HEATING:
                self._attr_hvac_action = HVACAction.HEATING
            elif prio in VALUES_PRIORITY_COOLING:
                self._attr_hvac_action = HVACAction.COOLING
            else:
                self._attr_hvac_action = HVACAction.IDLE
        else:
            self._attr_hvac_action = HVACAction.OFF

        self.async_write_ha_state()