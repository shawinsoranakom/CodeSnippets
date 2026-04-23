async def _async_update_data(self) -> int:
        try:
            response = await self._opensky.get_states(bounding_box=self._bounding_box)
        except OpenSkyError as exc:
            raise UpdateFailed from exc
        currently_tracked = set()
        flight_metadata: dict[str, StateVector] = {}
        for flight in response.states:
            if not flight.callsign:
                continue
            callsign = flight.callsign.strip()
            if callsign:
                flight_metadata[callsign] = flight
            else:
                continue
            if (
                flight.longitude is None
                or flight.latitude is None
                or flight.on_ground
                or flight.barometric_altitude is None
            ):
                continue
            altitude = flight.barometric_altitude
            if altitude > self._altitude and self._altitude != 0:
                continue
            currently_tracked.add(callsign)
        if self._previously_tracked is not None:
            entries = currently_tracked - self._previously_tracked
            exits = self._previously_tracked - currently_tracked
            self._handle_boundary(entries, EVENT_OPENSKY_ENTRY, flight_metadata)
            self._handle_boundary(exits, EVENT_OPENSKY_EXIT, flight_metadata)
        self._previously_tracked = currently_tracked

        return len(currently_tracked)