async def _async_update(self) -> None:
        """Update the entity state, including brightness and color temperature."""
        await super()._async_update()

        if not self._verify_active:
            return

        if self._brightness_address:
            brightness_result = await self._hub.async_pb_call(
                unit=self._device_address,
                value=1,
                address=self._brightness_address,
                use_call=CALL_TYPE_REGISTER_HOLDING,
            )

            if (
                brightness_result
                and brightness_result.registers
                and brightness_result.registers[0] != LIGHT_MODBUS_INVALID_VALUE
            ):
                self._attr_brightness = self._convert_modbus_percent_to_brightness(
                    brightness_result.registers[0]
                )

        if self._color_temp_address:
            color_result = await self._hub.async_pb_call(
                unit=self._device_address,
                value=1,
                address=self._color_temp_address,
                use_call=CALL_TYPE_REGISTER_HOLDING,
            )
            if (
                color_result
                and color_result.registers
                and color_result.registers[0] != LIGHT_MODBUS_INVALID_VALUE
            ):
                self._attr_color_temp_kelvin = (
                    self._convert_modbus_percent_to_temperature(
                        color_result.registers[0]
                    )
                )