def _find_next_trip(
        self, future_trips: list[Trip], first_trip: Trip
    ) -> Trip | None:
        """Find the next trip with a different departure time than the first trip."""
        next_trip = None
        if len(future_trips) > 1:
            first_time = (
                first_trip.departure_time_actual
                if first_trip.departure_time_actual is not None
                else first_trip.departure_time_planned
            )
            for trip in future_trips[1:]:
                trip_time = (
                    trip.departure_time_actual
                    if trip.departure_time_actual is not None
                    else trip.departure_time_planned
                )
                if trip_time and first_time and trip_time > first_time:
                    next_trip = trip
                    break
        return next_trip