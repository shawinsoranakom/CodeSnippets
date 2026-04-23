def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the vacuum cleaner."""
        data: dict[str, Any] = {}

        if self._status_state is not None:
            data[ATTR_STATUS] = self._status_state
        if self._clean_time_start is not None:
            data[ATTR_CLEAN_START] = self._clean_time_start
        if self._clean_time_stop is not None:
            data[ATTR_CLEAN_STOP] = self._clean_time_stop
        if self._clean_area is not None:
            data[ATTR_CLEAN_AREA] = self._clean_area
        if self._clean_susp_charge_count is not None:
            data[ATTR_CLEAN_SUSP_COUNT] = self._clean_susp_charge_count
        if self._clean_susp_time is not None:
            data[ATTR_CLEAN_SUSP_TIME] = self._clean_susp_time
        if self._clean_pause_time is not None:
            data[ATTR_CLEAN_PAUSE_TIME] = self._clean_pause_time
        if self._clean_error_time is not None:
            data[ATTR_CLEAN_ERROR_TIME] = self._clean_error_time
        if self._clean_battery_start is not None:
            data[ATTR_CLEAN_BATTERY_START] = self._clean_battery_start
        if self._clean_battery_end is not None:
            data[ATTR_CLEAN_BATTERY_END] = self._clean_battery_end
        if self._launched_from is not None:
            data[ATTR_LAUNCHED_FROM] = self._launched_from

        return data