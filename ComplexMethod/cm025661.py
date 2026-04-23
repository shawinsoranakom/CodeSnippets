def update(self) -> None:
        """Get the departure board."""
        try:
            self._departureboard = self._planner.departureboard(
                self._departure["station_id"],
                direction=self._heading["station_id"] if self._heading else None,
                date=now() + self._delay,
            )
        except vasttrafik.Error:
            _LOGGER.debug("Unable to read departure board, updating token")
            self._planner.update_token()

        if not self._departureboard:
            _LOGGER.debug(
                "No departures from departure station %s to destination station %s",
                self._departure["station_name"],
                self._heading["station_name"] if self._heading else "ANY",
            )
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
        else:
            for departure in self._departureboard:
                service_journey = departure.get("serviceJourney", {})
                line = service_journey.get("line", {})

                if departure.get("isCancelled"):
                    continue
                if not self._lines or line.get("shortName") in self._lines:
                    if "estimatedOtherwisePlannedTime" in departure:
                        try:
                            self._attr_native_value = datetime.fromisoformat(
                                departure["estimatedOtherwisePlannedTime"]
                            ).strftime("%H:%M")
                        except ValueError:
                            self._attr_native_value = departure[
                                "estimatedOtherwisePlannedTime"
                            ]
                    else:
                        self._attr_native_value = None

                    stop_point = departure.get("stopPoint", {})

                    params = {
                        ATTR_ACCESSIBILITY: "wheelChair"
                        if line.get("isWheelchairAccessible")
                        else None,
                        ATTR_DIRECTION: service_journey.get("direction"),
                        ATTR_LINE: line.get("shortName"),
                        ATTR_TRACK: stop_point.get("platform"),
                        ATTR_FROM: stop_point.get("name"),
                        ATTR_TO: self._heading["station_name"]
                        if self._heading
                        else "ANY",
                        ATTR_DELAY: self._delay.seconds // 60 % 60,
                    }

                    self._attr_extra_state_attributes = {
                        k: v for k, v in params.items() if v
                    }
                    break