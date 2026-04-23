def update(self) -> None:
        """Get the latest data from GTFS and update the states."""
        with self.lock:
            # Fetch valid stop information once
            if not self._origin:
                stops = self._pygtfs.stops_by_id(self.origin)
                if not stops:
                    self._available = False
                    _LOGGER.warning("Origin stop ID %s not found", self.origin)
                    return
                self._origin = stops[0]

            if not self._destination:
                stops = self._pygtfs.stops_by_id(self.destination)
                if not stops:
                    self._available = False
                    _LOGGER.warning(
                        "Destination stop ID %s not found", self.destination
                    )
                    return
                self._destination = stops[0]

            self._available = True

            # Fetch next departure
            self._departure = get_next_departure(
                self._pygtfs,
                self.origin,
                self.destination,
                self._offset,
                self._include_tomorrow,
            )

            # Fetch trip and route details once, unless updated
            if not self._departure:
                self._trip = None
            else:
                trip_id = self._departure["trip_id"]
                if not self._trip or self._trip.trip_id != trip_id:
                    _LOGGER.debug("Fetching trip details for %s", trip_id)
                    self._trip = self._pygtfs.trips_by_id(trip_id)[0]

                route_id = self._departure["route_id"]
                if not self._route or self._route.route_id != route_id:
                    _LOGGER.debug("Fetching route details for %s", route_id)
                    self._route = self._pygtfs.routes_by_id(route_id)[0]

            # Fetch agency details exactly once
            if self._agency is None and self._route:
                _LOGGER.debug("Fetching agency details for %s", self._route.agency_id)
                try:
                    self._agency = self._pygtfs.agencies_by_id(self._route.agency_id)[0]
                except IndexError:
                    _LOGGER.warning(
                        (
                            "Agency ID '%s' was not found in agency table, "
                            "you may want to update the routes database table "
                            "to fix this missing reference"
                        ),
                        self._route.agency_id,
                    )
                    self._agency = False

            # Define the state as a UTC timestamp with ISO 8601 format
            if not self._departure:
                self._state = None
            elif self._agency:
                self._state = self._departure["departure_time"].replace(
                    tzinfo=dt_util.get_time_zone(self._agency.agency_timezone)
                )
            else:
                self._state = self._departure["departure_time"].replace(
                    tzinfo=dt_util.UTC
                )

            # Assign attributes, icon and name
            self.update_attributes()

            if self._agency:
                self._attr_attribution = self._agency.agency_name
            else:
                self._attr_attribution = None

            if self._route:
                self._icon = ICONS.get(self._route.route_type, ICON)
            else:
                self._icon = ICON

            name = (
                f"{getattr(self._agency, 'agency_name', DEFAULT_NAME)} "
                f"{self.origin} to {self.destination} next departure"
            )
            if not self._departure:
                name = f"{DEFAULT_NAME}"
            self._name = self._custom_name or name