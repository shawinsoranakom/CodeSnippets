async def _async_update(self) -> None:
        """Update the state of the sensor."""
        raw_result = await self._hub.async_pb_call(
            self._device_address, self._address, self._count, self._input_type
        )
        if raw_result is None:
            self._attr_available = False
            self._attr_native_value = None
            if self._coordinator:
                self._coordinator.async_set_updated_data(None)
            self.async_write_ha_state()
            return
        self._attr_available = True
        result = self.unpack_structure_result(
            raw_result.registers, self._scale, self._offset
        )
        if self._coordinator:
            result_array: list[float | None] = []
            if result:
                for i in result.split(","):
                    if i != "None":
                        result_array.append(
                            float(i) if not self._value_is_int else int(i)
                        )
                    else:
                        result_array.append(None)

                self._attr_native_value = result_array[0]
                self._coordinator.async_set_updated_data(result_array)
            else:
                self._attr_native_value = None
                result_array = (self._slave_count + 1) * [None]
                self._coordinator.async_set_updated_data(result_array)
        else:
            self._attr_native_value = result
        self.async_write_ha_state()