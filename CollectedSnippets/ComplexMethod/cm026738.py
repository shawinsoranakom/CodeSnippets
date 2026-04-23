def update_events(self, now: datetime | None = None) -> None:
        """Update the attributes containing solar events."""
        # Grab current time in case system clock changed since last time we ran.
        utc_point_in_time = dt_util.utcnow()
        self._next_change = utc_point_in_time + timedelta(days=400)

        # Work our way around the solar cycle, figure out the next
        # phase. Some of these are stored.
        self.location.solar_depression = "astronomical"
        self._check_event(utc_point_in_time, "dawn", PHASE_NIGHT)
        self.location.solar_depression = "nautical"
        self._check_event(utc_point_in_time, "dawn", PHASE_ASTRONOMICAL_TWILIGHT)
        self.location.solar_depression = "civil"
        self.next_dawn = self._check_event(
            utc_point_in_time, "dawn", PHASE_NAUTICAL_TWILIGHT
        )
        self.next_rising = self._check_event(
            utc_point_in_time, SUN_EVENT_SUNRISE, PHASE_TWILIGHT
        )
        self.location.solar_depression = -10
        self._check_event(utc_point_in_time, "dawn", PHASE_SMALL_DAY)
        self.next_noon = self._check_event(utc_point_in_time, "noon", None)
        self._check_event(utc_point_in_time, "dusk", PHASE_DAY)
        self.next_setting = self._check_event(
            utc_point_in_time, SUN_EVENT_SUNSET, PHASE_SMALL_DAY
        )
        self.location.solar_depression = "civil"
        self.next_dusk = self._check_event(utc_point_in_time, "dusk", PHASE_TWILIGHT)
        self.location.solar_depression = "nautical"
        self._check_event(utc_point_in_time, "dusk", PHASE_NAUTICAL_TWILIGHT)
        self.location.solar_depression = "astronomical"
        self._check_event(utc_point_in_time, "dusk", PHASE_ASTRONOMICAL_TWILIGHT)
        self.next_midnight = self._check_event(utc_point_in_time, "midnight", None)
        self.location.solar_depression = "civil"

        # if the event was solar midday or midnight, phase will now
        # be None. Solar noon doesn't always happen when the sun is
        # even in the day at the poles, so we can't rely on it.
        # Need to calculate phase if next is noon or midnight
        if self.phase is None:
            elevation = self.location.solar_elevation(self._next_change, self.elevation)
            if elevation >= 10:
                self.phase = PHASE_DAY
            elif elevation >= 0:
                self.phase = PHASE_SMALL_DAY
            elif elevation >= -6:
                self.phase = PHASE_TWILIGHT
            elif elevation >= -12:
                self.phase = PHASE_NAUTICAL_TWILIGHT
            elif elevation >= -18:
                self.phase = PHASE_ASTRONOMICAL_TWILIGHT
            else:
                self.phase = PHASE_NIGHT

        self.rising = self.next_noon < self.next_midnight

        _LOGGER.debug(
            "sun phase_update@%s: phase=%s", utc_point_in_time.isoformat(), self.phase
        )
        if self._update_sun_position_listener:
            self._update_sun_position_listener()
        self.update_sun_position()
        async_dispatcher_send(self.hass, SIGNAL_EVENTS_CHANGED)

        # Set timer for the next solar event
        self._update_events_listener = event.async_track_point_in_utc_time(
            self.hass, self.update_events, self._next_change
        )
        _LOGGER.debug("next time: %s", self._next_change.isoformat())