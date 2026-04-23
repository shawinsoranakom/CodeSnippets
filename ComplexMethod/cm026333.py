async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Priority 1: Initial value
        if self.state is not None:
            return

        default_value = py_datetime.datetime.today().strftime(f"{FMT_DATE} 00:00:00")

        # Priority 2: Old state
        if (old_state := await self.async_get_last_state()) is None:
            self._current_datetime = dt_util.parse_datetime(default_value)
            return

        if self.has_date and self.has_time:
            date_time = dt_util.parse_datetime(old_state.state)
            if date_time is None:
                current_datetime = dt_util.parse_datetime(default_value)
            else:
                current_datetime = date_time

        elif self.has_date:
            if (date := dt_util.parse_date(old_state.state)) is None:
                current_datetime = dt_util.parse_datetime(default_value)
            else:
                current_datetime = py_datetime.datetime.combine(date, DEFAULT_TIME)

        elif (time := dt_util.parse_time(old_state.state)) is None:
            current_datetime = dt_util.parse_datetime(default_value)
        else:
            current_datetime = py_datetime.datetime.combine(
                py_datetime.date.today(), time
            )

        self._current_datetime = current_datetime.replace(
            tzinfo=dt_util.get_default_time_zone()
        )