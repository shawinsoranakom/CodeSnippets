async def async_update(self, **kwargs: Any) -> None:
        """Update the sensor."""
        departure_time = utcnow() + timedelta(
            minutes=self.config_entry.options.get(CONF_OFFSET, 0)
        )

        departure_time_tz_berlin = departure_time.astimezone(BERLIN_TIME_ZONE)

        station = self.config_entry.data[CONF_STATION]

        payload = {
            "station": {"id": station["id"], "type": station["type"]},
            "time": {
                "date": departure_time_tz_berlin.strftime("%d.%m.%Y"),
                "time": departure_time_tz_berlin.strftime("%H:%M"),
            },
            "maxList": MAX_LIST,
            "maxTimeOffset": MAX_TIME_OFFSET,
            "useRealtime": self.config_entry.options.get(CONF_REAL_TIME, False),
        }

        if "filter" in self.config_entry.options:
            payload.update({"filter": self.config_entry.options["filter"]})

        try:
            data = await self.gti.departureList(payload)
        except InvalidAuth as error:
            if self._last_error != InvalidAuth:
                _LOGGER.error("Authentication failed: %r", error)
                self._last_error = InvalidAuth
            self._attr_available = False
        except ClientConnectorError as error:
            if self._last_error != ClientConnectorError:
                _LOGGER.warning("Network unavailable: %r", error)
                self._last_error = ClientConnectorError
            self._attr_available = False
        except Exception as error:  # noqa: BLE001
            if self._last_error != error:
                _LOGGER.error("Error occurred while fetching data: %r", error)
                self._last_error = error
            self._attr_available = False

        if not (data["returnCode"] == "OK" and data.get("departures")):
            self._attr_available = False
            return

        if self._last_error == ClientConnectorError:
            _LOGGER.debug("Network available again")

        self._last_error = None

        departure = data["departures"][0]
        line = departure["line"]
        delay = departure.get("delay", 0)
        cancelled = departure.get("cancelled", False)
        extra = departure.get("extra", False)
        self._attr_available = True
        self._attr_native_value = (
            departure_time
            + timedelta(minutes=departure["timeOffset"])
            + timedelta(seconds=delay)
        )

        self._attr_extra_state_attributes.update(
            {
                ATTR_LINE: line["name"],
                ATTR_ORIGIN: line["origin"],
                ATTR_DIRECTION: line["direction"],
                ATTR_TYPE: line["type"]["shortInfo"],
                ATTR_ID: line["id"],
                ATTR_DELAY: delay,
                ATTR_CANCELLED: cancelled,
                ATTR_EXTRA: extra,
            }
        )

        departures = []
        for departure in data["departures"]:
            line = departure["line"]
            delay = departure.get("delay", 0)
            cancelled = departure.get("cancelled", False)
            extra = departure.get("extra", False)
            departures.append(
                {
                    ATTR_DEPARTURE: departure_time
                    + timedelta(minutes=departure["timeOffset"])
                    + timedelta(seconds=delay),
                    ATTR_LINE: line["name"],
                    ATTR_ORIGIN: line["origin"],
                    ATTR_DIRECTION: line["direction"],
                    ATTR_TYPE: line["type"]["shortInfo"],
                    ATTR_ID: line["id"],
                    ATTR_DELAY: delay,
                    ATTR_CANCELLED: cancelled,
                    ATTR_EXTRA: extra,
                }
            )
        self._attr_extra_state_attributes[ATTR_NEXT] = departures