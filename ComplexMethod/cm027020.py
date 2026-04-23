def _remove_trips_in_the_past(self, trips: list[Trip]) -> list[Trip]:
        """Filter out trips that have already departed."""
        # Compare against Dutch local time to align with ns_api timezone handling
        now = _current_time_nl()
        future_trips = []
        for trip in trips:
            departure_time = (
                trip.departure_time_actual
                if trip.departure_time_actual is not None
                else trip.departure_time_planned
            )
            if departure_time is not None and (
                departure_time.tzinfo is None
                or departure_time.tzinfo.utcoffset(departure_time) is None
            ):
                # Make naive datetimes timezone-aware using current reference tz
                departure_time = departure_time.replace(tzinfo=now.tzinfo)

            if departure_time and departure_time > now:
                future_trips.append(trip)
        return future_trips