async def update(self):
        """Update the connection data."""
        if self._station_id is None:
            try:
                station = await MvgApi.station_async(self._station_name)
                self._station_id = station["id"]
            except MvgApiError as err:
                _LOGGER.error(
                    "Failed to resolve station %s: %s", self._station_name, err
                )
                self.departures = []
                return

        try:
            _departures = await MvgApi.departures_async(
                station_id=self._station_id,
                offset=self._timeoffset,
                limit=self._number,
                transport_types=[
                    transport_type
                    for transport_type in TransportType
                    if transport_type.value[0] in self._products
                ]
                if self._products
                else None,
            )
        except ValueError:
            self.departures = []
            _LOGGER.warning("Returned data not understood")
            return
        self.departures = []
        for _departure in _departures:
            if (
                "" not in self._destinations[:1]
                and _departure["destination"] not in self._destinations
            ):
                continue

            if "" not in self._lines[:1] and _departure["line"] not in self._lines:
                continue

            time_to_departure = _get_minutes_until_departure(_departure["time"])

            if time_to_departure < self._timeoffset:
                continue

            _nextdep = {}
            for k in ("destination", "line", "type", "cancelled", "icon"):
                _nextdep[k] = _departure.get(k, "")
            _nextdep["time_in_mins"] = time_to_departure
            self.departures.append(_nextdep)