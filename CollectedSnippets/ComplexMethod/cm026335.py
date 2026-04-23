def async_set_datetime(self, date=None, time=None, datetime=None, timestamp=None):
        """Set a new date / time."""
        if timestamp is not None:
            datetime = dt_util.as_local(dt_util.utc_from_timestamp(timestamp))

        if datetime:
            date = datetime.date()
            time = datetime.time()

        if not self.has_date:
            date = None

        if not self.has_time:
            time = None

        if not date and not time:
            raise vol.Invalid("Nothing to set")

        if not date:
            date = self._current_datetime.date()

        if not time:
            time = self._current_datetime.time()

        self._current_datetime = py_datetime.datetime.combine(
            date, time, dt_util.get_default_time_zone()
        )
        self.async_write_ha_state()