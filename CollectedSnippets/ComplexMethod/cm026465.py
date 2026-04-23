def _update_state(self) -> None:
        """Update the state."""
        latest_non_gps_home = latest_not_home = latest_gps = latest = coordinates = None
        for entity_id in self._config[CONF_DEVICE_TRACKERS]:
            state = self.hass.states.get(entity_id)

            if not state or state.state in IGNORE_STATES:
                continue

            if state.attributes.get(ATTR_SOURCE_TYPE) == SourceType.GPS:
                latest_gps = _get_latest(latest_gps, state)
            elif state.state == STATE_HOME:
                latest_non_gps_home = _get_latest(latest_non_gps_home, state)
            else:
                latest_not_home = _get_latest(latest_not_home, state)

        if latest_non_gps_home:
            latest = latest_non_gps_home
            if (
                latest_non_gps_home.attributes.get(ATTR_LATITUDE) is None
                and latest_non_gps_home.attributes.get(ATTR_LONGITUDE) is None
                and (home_zone := self.hass.states.get(ENTITY_ID_HOME))
            ):
                coordinates = home_zone
            else:
                coordinates = latest_non_gps_home
        elif latest_gps:
            latest = latest_gps
            coordinates = latest_gps
        else:
            latest = latest_not_home
            coordinates = latest_not_home

        if latest and coordinates:
            self._parse_source_state(latest, coordinates)
        else:
            self._attr_state = None
            self._source = None
            self._latitude = None
            self._longitude = None
            self._gps_accuracy = None
            self._in_zones = []

        self._update_extra_state_attributes()
        self.async_write_ha_state()