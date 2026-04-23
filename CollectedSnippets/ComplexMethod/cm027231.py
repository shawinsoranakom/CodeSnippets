async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if self._hvac_onoff_register is not None:
            # Turn HVAC Off by writing self._hvac_off_value to the On/Off
            # register, or self._hvac_on_value otherwise.
            if self._hvac_onoff_write_registers:
                await self._hub.async_pb_call(
                    self._device_address,
                    self._hvac_onoff_register,
                    [
                        self._hvac_off_value
                        if hvac_mode == HVACMode.OFF
                        else self._hvac_on_value
                    ],
                    CALL_TYPE_WRITE_REGISTERS,
                )
            else:
                await self._hub.async_pb_call(
                    self._device_address,
                    self._hvac_onoff_register,
                    self._hvac_off_value
                    if hvac_mode == HVACMode.OFF
                    else self._hvac_on_value,
                    CALL_TYPE_WRITE_REGISTER,
                )

        if self._hvac_onoff_coil is not None:
            # Turn HVAC Off by writing 0 to the On/Off coil, or 1 otherwise.
            await self._hub.async_pb_call(
                self._device_address,
                self._hvac_onoff_coil,
                0 if hvac_mode == HVACMode.OFF else 1,
                CALL_TYPE_WRITE_COIL,
            )

        if self._hvac_mode_register is not None:
            # Write a value to the mode register for the desired mode.
            for value, mode in self._hvac_mode_mapping:
                if mode == hvac_mode:
                    if self._hvac_mode_write_registers:
                        await self._hub.async_pb_call(
                            self._device_address,
                            self._hvac_mode_register,
                            [value],
                            CALL_TYPE_WRITE_REGISTERS,
                        )
                    else:
                        await self._hub.async_pb_call(
                            self._device_address,
                            self._hvac_mode_register,
                            value,
                            CALL_TYPE_WRITE_REGISTER,
                        )
                    break

        await self.async_local_update(cancel_pending_update=True)