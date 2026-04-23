async def _async_update(self) -> None:
        """Update Target & Current Temperature."""
        self._attr_target_temperature = await self._async_read_register(
            CALL_TYPE_REGISTER_HOLDING,
            self._target_temperature_register[
                HVACMODE_TO_TARG_TEMP_REG_INDEX_ARRAY[self._attr_hvac_mode]
            ],
            self._target_temp_scale,
            self._target_temp_offset,
        )

        self._attr_current_temperature = await self._async_read_register(
            self._input_type,
            self._address,
            self._current_temp_scale,
            self._current_temp_offset,
        )

        # Read the HVAC mode register if defined
        if self._hvac_mode_register is not None:
            hvac_mode = await self._async_read_register(
                CALL_TYPE_REGISTER_HOLDING,
                self._hvac_mode_register,
                DEFAULT_SCALE,
                DEFAULT_OFFSET,
                raw=True,
            )

            # Translate the value received
            if hvac_mode is not None:
                self._attr_hvac_mode = None
                for value, mode in self._hvac_mode_mapping:
                    if hvac_mode == value:
                        self._attr_hvac_mode = mode
                        break
        else:
            # since there are no hvac_mode_register, this
            # integration should not touch the attr.
            # However it lacks in the climate component.
            self._attr_hvac_mode = HVACMode.AUTO

        # Read the HVAC action register if defined
        if self._hvac_action_register is not None:
            hvac_action = await self._async_read_register(
                self._hvac_action_type,
                self._hvac_action_register,
                DEFAULT_SCALE,
                DEFAULT_OFFSET,
                raw=True,
            )

            # Translate the value received
            if hvac_action is not None:
                self._attr_hvac_action = None
                for value, action in self._hvac_action_mapping:
                    if hvac_action == value:
                        self._attr_hvac_action = action
                        break

        # Read the Fan mode register if defined
        if self._fan_mode_register is not None:
            fan_mode = await self._async_read_register(
                CALL_TYPE_REGISTER_HOLDING,
                self._fan_mode_register
                if isinstance(self._fan_mode_register, int)
                else self._fan_mode_register[0],
                DEFAULT_SCALE,
                DEFAULT_OFFSET,
                raw=True,
            )

            # Translate the value received
            if fan_mode is not None:
                self._attr_fan_mode = self._fan_mode_mapping_from_modbus.get(
                    int(fan_mode), self._attr_fan_mode
                )

        # Read the Swing mode register if defined
        if self._swing_mode_register:
            swing_mode = await self._async_read_register(
                CALL_TYPE_REGISTER_HOLDING,
                self._swing_mode_register
                if isinstance(self._swing_mode_register, int)
                else self._swing_mode_register[0],
                DEFAULT_SCALE,
                DEFAULT_OFFSET,
                raw=True,
            )

            self._attr_swing_mode = STATE_UNKNOWN
            for value, smode in self._swing_mode_modbus_mapping:
                if swing_mode == value:
                    self._attr_swing_mode = smode
                    break

            if self._attr_swing_mode is STATE_UNKNOWN:
                _err = f"{self.name}: No answer received from Swing mode register. State is Unknown"
                _LOGGER.error(_err)

        # Read the on/off register if defined. If the value in this
        # register is "OFF", it will take precedence over the value
        # in the mode register.
        if self._hvac_onoff_register is not None:
            onoff = await self._async_read_register(
                CALL_TYPE_REGISTER_HOLDING,
                self._hvac_onoff_register,
                DEFAULT_SCALE,
                DEFAULT_OFFSET,
                raw=True,
            )
            if onoff == self._hvac_off_value:
                self._attr_hvac_mode = HVACMode.OFF

        if self._hvac_onoff_coil is not None:
            onoff = await self._async_read_coil(self._hvac_onoff_coil)
            if onoff == 0:
                self._attr_hvac_mode = HVACMode.OFF