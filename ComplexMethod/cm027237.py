def unpack_structure_result(
        self,
        registers: list[int],
        scale: float = DEFAULT_SCALE,
        offset: float = DEFAULT_OFFSET,
    ) -> str | None:
        """Convert registers to proper result."""

        if self._swap:
            registers = self._swap_registers(
                copy.deepcopy(registers), self._slave_count
            )
        byte_string = b"".join([x.to_bytes(2, byteorder="big") for x in registers])
        if self._data_type == DataType.STRING:
            return byte_string.decode()
        if byte_string == b"nan\x00":
            return None

        try:
            val = struct.unpack(self._structure, byte_string)
        except struct.error as err:
            recv_size = len(registers) * 2
            msg = f"Received {recv_size} bytes, unpack error {err}"
            _LOGGER.error(msg)
            return None
        if len(val) > 1:
            # Apply scale, precision, limits to floats and ints
            v_result = []
            for entry in val:
                v_temp = self.__process_raw_value(entry, scale, offset)
                if self._data_type != DataType.CUSTOM:
                    v_result.append(str(v_temp))
                else:
                    v_result.append(str(v_temp) if v_temp is not None else "0")
            return ",".join(map(str, v_result))

        # Apply scale, precision, limits to floats and ints
        return self.__process_raw_value(val[0], scale, offset)