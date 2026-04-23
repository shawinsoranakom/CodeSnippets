def _calculate_boundary_time(self) -> None:
        """Calculate internal absolute time boundaries."""
        nowutc = dt_util.utcnow()
        # If after value is a sun event instead of absolute time
        if _is_sun_event(self._after):
            # Calculate the today's event utc time or
            # if not available take next
            after_event_date = get_astral_event_date(
                self.hass, self._after, nowutc
            ) or get_astral_event_next(self.hass, self._after, nowutc)
        else:
            # Convert local time provided to UTC today
            # datetime.combine(date, time, tzinfo) is not supported
            # in python 3.5. The self._after is provided
            # with hass configured TZ not system wide
            after_event_date = self._naive_time_to_utc_datetime(self._after)

        self._time_after = after_event_date

        # If before value is a sun event instead of absolute time
        if _is_sun_event(self._before):
            # Calculate the today's event utc time or  if not available take
            # next
            before_event_date = get_astral_event_date(
                self.hass, self._before, nowutc
            ) or get_astral_event_next(self.hass, self._before, nowutc)
            # Before is earlier than after
            if before_event_date < after_event_date:
                # Take next day for before
                before_event_date = get_astral_event_next(
                    self.hass, self._before, after_event_date
                )
        else:
            # Convert local time provided to UTC today, see above
            before_event_date = self._naive_time_to_utc_datetime(self._before)

            # It is safe to add timedelta days=1 to UTC as there is no DST
            if before_event_date < after_event_date + self._after_offset:
                before_event_date += timedelta(days=1)

        self._time_before = before_event_date

        # We are calculating the _time_after value assuming that it will happen today
        # But that is not always true, e.g. after 23:00, before 12:00 and now is 10:00
        # If _time_before and _time_after are ahead of nowutc:
        # _time_before is set to 12:00 next day
        # _time_after is set to 23:00 today
        # nowutc is set to 10:00 today

        if (
            not _is_sun_event(self._after)
            and self._time_after > nowutc
            and self._time_before > nowutc + timedelta(days=1)
        ):
            # remove one day from _time_before and _time_after
            self._time_after -= timedelta(days=1)
            self._time_before -= timedelta(days=1)

        # Add offset to utc boundaries according to the configuration
        self._time_after += self._after_offset
        self._time_before += self._before_offset