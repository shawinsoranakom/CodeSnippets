def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs: dict[str, Any] = {
            ATTR_EDITABLE: self.editable,
        }

        if self._current_datetime is None:
            return attrs

        if self.has_date and self._current_datetime is not None:
            attrs["year"] = self._current_datetime.year
            attrs["month"] = self._current_datetime.month
            attrs["day"] = self._current_datetime.day

        if self.has_time and self._current_datetime is not None:
            attrs["hour"] = self._current_datetime.hour
            attrs["minute"] = self._current_datetime.minute
            attrs["second"] = self._current_datetime.second

        if not self.has_date:
            attrs["timestamp"] = (
                self._current_datetime.hour * 3600
                + self._current_datetime.minute * 60
                + self._current_datetime.second
            )

        elif not self.has_time:
            extended = py_datetime.datetime.combine(
                self._current_datetime, py_datetime.time(0, 0)
            )
            attrs["timestamp"] = extended.timestamp()

        else:
            attrs["timestamp"] = self._current_datetime.timestamp()

        return attrs