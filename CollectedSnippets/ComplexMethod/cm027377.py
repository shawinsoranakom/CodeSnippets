def update_attributes(self) -> None:
        """Update state attributes."""
        # Add departure information
        if self._departure:
            self._attributes[ATTR_ARRIVAL] = dt_util.as_utc(
                self._departure["arrival_time"]
            ).isoformat()

            self._attributes[ATTR_DAY] = self._departure["day"]

            if self._departure[ATTR_FIRST] is not None:
                self._attributes[ATTR_FIRST] = self._departure["first"]
            elif ATTR_FIRST in self._attributes:
                del self._attributes[ATTR_FIRST]

            if self._departure[ATTR_LAST] is not None:
                self._attributes[ATTR_LAST] = self._departure["last"]
            elif ATTR_LAST in self._attributes:
                del self._attributes[ATTR_LAST]
        else:
            if ATTR_ARRIVAL in self._attributes:
                del self._attributes[ATTR_ARRIVAL]
            if ATTR_DAY in self._attributes:
                del self._attributes[ATTR_DAY]
            if ATTR_FIRST in self._attributes:
                del self._attributes[ATTR_FIRST]
            if ATTR_LAST in self._attributes:
                del self._attributes[ATTR_LAST]

        # Add contextual information
        self._attributes[ATTR_OFFSET] = self._offset.total_seconds() / 60

        if self._state is None:
            self._attributes[ATTR_INFO] = (
                "No more departures"
                if self._include_tomorrow
                else "No more departures today"
            )
        elif ATTR_INFO in self._attributes:
            del self._attributes[ATTR_INFO]

        # Add extra metadata
        key = "agency_id"
        if self._agency and key not in self._attributes:
            self.append_keys(self.dict_for_table(self._agency), "Agency")

        key = "origin_station_stop_id"
        if self._origin and key not in self._attributes:
            self.append_keys(self.dict_for_table(self._origin), "Origin Station")
            self._attributes[ATTR_LOCATION_ORIGIN] = LOCATION_TYPE_OPTIONS.get(
                self._origin.location_type, LOCATION_TYPE_DEFAULT
            )
            self._attributes[ATTR_WHEELCHAIR_ORIGIN] = WHEELCHAIR_BOARDING_OPTIONS.get(
                self._origin.wheelchair_boarding, WHEELCHAIR_BOARDING_DEFAULT
            )

        key = "destination_station_stop_id"
        if self._destination and key not in self._attributes:
            self.append_keys(
                self.dict_for_table(self._destination), "Destination Station"
            )
            self._attributes[ATTR_LOCATION_DESTINATION] = LOCATION_TYPE_OPTIONS.get(
                self._destination.location_type, LOCATION_TYPE_DEFAULT
            )
            self._attributes[ATTR_WHEELCHAIR_DESTINATION] = (
                WHEELCHAIR_BOARDING_OPTIONS.get(
                    self._destination.wheelchair_boarding, WHEELCHAIR_BOARDING_DEFAULT
                )
            )

        # Manage Route metadata
        key = "route_id"
        if not self._route and key in self._attributes:
            self.remove_keys("Route")
        elif self._route and (
            key not in self._attributes or self._attributes[key] != self._route.route_id
        ):
            self.append_keys(self.dict_for_table(self._route), "Route")
            self._attributes[ATTR_ROUTE_TYPE] = ROUTE_TYPE_OPTIONS[
                self._route.route_type
            ]

        # Manage Trip metadata
        key = "trip_id"
        if not self._trip and key in self._attributes:
            self.remove_keys("Trip")
        elif self._trip and (
            key not in self._attributes or self._attributes[key] != self._trip.trip_id
        ):
            self.append_keys(self.dict_for_table(self._trip), "Trip")
            self._attributes[ATTR_BICYCLE] = BICYCLE_ALLOWED_OPTIONS.get(
                self._trip.bikes_allowed, BICYCLE_ALLOWED_DEFAULT
            )
            self._attributes[ATTR_WHEELCHAIR] = WHEELCHAIR_ACCESS_OPTIONS.get(
                self._trip.wheelchair_accessible, WHEELCHAIR_ACCESS_DEFAULT
            )

        # Manage Stop Times metadata
        prefix = "origin_stop"
        if self._departure:
            self.append_keys(self._departure["origin_stop_time"], prefix)
            self._attributes[ATTR_DROP_OFF_ORIGIN] = DROP_OFF_TYPE_OPTIONS.get(
                self._departure["origin_stop_time"]["Drop Off Type"],
                DROP_OFF_TYPE_DEFAULT,
            )
            self._attributes[ATTR_PICKUP_ORIGIN] = PICKUP_TYPE_OPTIONS.get(
                self._departure["origin_stop_time"]["Pickup Type"], PICKUP_TYPE_DEFAULT
            )
            self._attributes[ATTR_TIMEPOINT_ORIGIN] = TIMEPOINT_OPTIONS.get(
                self._departure["origin_stop_time"]["Timepoint"], TIMEPOINT_DEFAULT
            )
        else:
            self.remove_keys(prefix)

        prefix = "destination_stop"
        if self._departure:
            self.append_keys(self._departure["destination_stop_time"], prefix)
            self._attributes[ATTR_DROP_OFF_DESTINATION] = DROP_OFF_TYPE_OPTIONS.get(
                self._departure["destination_stop_time"]["Drop Off Type"],
                DROP_OFF_TYPE_DEFAULT,
            )
            self._attributes[ATTR_PICKUP_DESTINATION] = PICKUP_TYPE_OPTIONS.get(
                self._departure["destination_stop_time"]["Pickup Type"],
                PICKUP_TYPE_DEFAULT,
            )
            self._attributes[ATTR_TIMEPOINT_DESTINATION] = TIMEPOINT_OPTIONS.get(
                self._departure["destination_stop_time"]["Timepoint"], TIMEPOINT_DEFAULT
            )
        else:
            self.remove_keys(prefix)