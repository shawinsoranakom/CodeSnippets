async def low_level_pb_call(
        self, slave: int | None, address: int, value: int | list[int], use_call: str
    ) -> ModbusPDU | None:
        """Call sync. pymodbus."""
        kwargs: dict[str, Any] = (
            {DEVICE_ID: slave} if slave is not None else {DEVICE_ID: 1}
        )
        entry = self._pb_request[use_call]

        if use_call in {"write_registers", "write_coils"}:
            if not isinstance(value, list):
                value = [value]

        kwargs[entry.value_attr_name] = value
        try:
            result: ModbusPDU = await entry.func(address, **kwargs)
        except ModbusException as exception_error:
            error = f"Error: device: {slave} address: {address} -> {exception_error!s}"
            self._log_error(error)
            return None
        if not result:
            error = (
                f"Error: device: {slave} address: {address} -> pymodbus returned None"
            )
            self._log_error(error)
            return None
        if not hasattr(result, entry.attr):
            error = f"Error: device: {slave} address: {address} -> {result!s}"
            self._log_error(error)
            return None
        if result.isError():
            error = f"Error: device: {slave} address: {address} -> pymodbus returned isError True"
            self._log_error(error)
            return None
        return result