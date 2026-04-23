def __process_raw_value(
        self,
        entry: float | bytes,
        scale: float = DEFAULT_SCALE,
        offset: float = DEFAULT_OFFSET,
    ) -> str | None:
        """Process value from sensor with NaN handling, scaling, offset, min/max etc."""
        if self._nan_value is not None and entry in (self._nan_value, -self._nan_value):
            return None
        if isinstance(entry, bytes):
            return entry.decode()
        if entry != entry:  # noqa: PLR0124
            # NaN float detection replace with None
            return None
        val: float | int = scale * entry + offset
        if self._min_value is not None and val < self._min_value:
            val = self._min_value
        if self._max_value is not None and val > self._max_value:
            val = self._max_value
        if self._zero_suppress is not None and abs(val) <= self._zero_suppress:
            return "0"
        if self._precision == 0:
            return str(round(val))
        return f"{float(val):.{self._precision}f}"