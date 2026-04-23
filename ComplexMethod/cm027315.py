def _process_update_extra_state_attributes(
        self, extra_state_attributes: dict[str, Any]
    ) -> None:
        """Extract the location from the extra state attributes."""
        if (
            ATTR_LATITUDE in extra_state_attributes
            or ATTR_LONGITUDE in extra_state_attributes
        ):
            latitude: float | None
            longitude: float | None
            gps_accuracy: float
            if isinstance(
                latitude := extra_state_attributes.get(ATTR_LATITUDE), (int, float)
            ) and isinstance(
                longitude := extra_state_attributes.get(ATTR_LONGITUDE), (int, float)
            ):
                self._attr_latitude = latitude
                self._attr_longitude = longitude
            else:
                # Invalid or incomplete coordinates, reset location
                self._attr_latitude = None
                self._attr_longitude = None
                _LOGGER.warning(
                    "Extra state attributes received at % and template %s "
                    "contain invalid or incomplete location info. Got %s",
                    self._config.get(CONF_JSON_ATTRS_TEMPLATE),
                    self._config.get(CONF_JSON_ATTRS_TOPIC),
                    extra_state_attributes,
                )

            if ATTR_GPS_ACCURACY in extra_state_attributes:
                if isinstance(
                    gps_accuracy := extra_state_attributes[ATTR_GPS_ACCURACY],
                    (int, float),
                ):
                    self._attr_location_accuracy = gps_accuracy
                else:
                    _LOGGER.warning(
                        "Extra state attributes received at % and template %s "
                        "contain invalid GPS accuracy setting, "
                        "gps_accuracy was set to 0 as the default. Got %s",
                        self._config.get(CONF_JSON_ATTRS_TEMPLATE),
                        self._config.get(CONF_JSON_ATTRS_TOPIC),
                        extra_state_attributes,
                    )
                    self._attr_location_accuracy = 0

            else:
                self._attr_location_accuracy = 0

        self._attr_extra_state_attributes = {
            attribute: value
            for attribute, value in extra_state_attributes.items()
            if attribute not in {ATTR_GPS_ACCURACY, ATTR_LATITUDE, ATTR_LONGITUDE}
        }