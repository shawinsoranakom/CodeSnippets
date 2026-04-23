def _update(self, _: datetime | None = None) -> None:
        """Update the states of the schedule."""
        now = dt_util.now()
        todays_schedule = self._config.get(WEEKDAY_TO_CONF[now.weekday()], [])

        # Determine current schedule state
        for time_range in todays_schedule:
            # The current time should be greater or equal to CONF_FROM.
            if now.time() < time_range[CONF_FROM]:
                continue
            # The current time should be smaller (and not equal) to CONF_TO.
            # Note that any time in the day is treated as smaller than time.max.
            if now.time() < time_range[CONF_TO] or time_range[CONF_TO] == time.max:
                self._attr_state = STATE_ON
                current_data = time_range.get(CONF_DATA)
                break
        else:
            self._attr_state = STATE_OFF
            current_data = None

        # Find next event in the schedule, loop over each day (starting with
        # the current day) until the next event has been found.
        next_event = None
        for day in range(8):  # 8 because we need to search today's weekday next week
            day_schedule = self._config.get(
                WEEKDAY_TO_CONF[(now.weekday() + day) % 7], []
            )
            times = sorted(
                itertools.chain(
                    *[
                        [time_range[CONF_FROM], time_range[CONF_TO]]
                        for time_range in day_schedule
                    ]
                )
            )

            if next_event := next(
                (
                    possible_next_event
                    for timestamp in times
                    if (
                        possible_next_event := (
                            datetime.combine(now.date(), timestamp, tzinfo=now.tzinfo)
                            + timedelta(days=day)
                            if timestamp != time.max
                            # Special case for midnight of the following day.
                            else datetime.combine(now.date(), time(), tzinfo=now.tzinfo)
                            + timedelta(days=day + 1)
                        )
                    )
                    > now
                ),
                None,
            ):
                # We have found the next event in this day, stop searching.
                break

        self._attr_extra_state_attributes = {
            ATTR_NEXT_EVENT: next_event,
        }

        if current_data:
            # Add each key/value pair in the data to the entity's state attributes
            self._attr_extra_state_attributes.update(current_data)

        self.async_write_ha_state()

        if next_event:
            self._unsub_update = async_track_point_in_utc_time(
                self.hass,
                self._update,
                next_event,
            )