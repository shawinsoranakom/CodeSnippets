def _calc_direction_of_travel(
        self,
        zone: State,
        device: State,
        old_latitude: float | None,
        old_longitude: float | None,
        new_latitude: float | None,
        new_longitude: float | None,
    ) -> str | None:
        if device.state.lower() == self.proximity_zone_name.lower():
            _LOGGER.debug(
                "%s: %s in zone -> direction_of_travel=arrived",
                self.name,
                device.entity_id,
            )
            return "arrived"

        if (
            old_latitude is None
            or old_longitude is None
            or new_latitude is None
            or new_longitude is None
        ):
            return None

        old_distance = distance(
            zone.attributes[ATTR_LATITUDE],
            zone.attributes[ATTR_LONGITUDE],
            old_latitude,
            old_longitude,
        )
        new_distance = distance(
            zone.attributes[ATTR_LATITUDE],
            zone.attributes[ATTR_LONGITUDE],
            new_latitude,
            new_longitude,
        )

        # it is ensured, that distance can't be None, since zones must have lat/lon coordinates
        assert old_distance is not None
        assert new_distance is not None
        distance_travelled = round(new_distance - old_distance, 1)

        if distance_travelled < self.tolerance * -1:
            return "towards"

        if distance_travelled > self.tolerance:
            return "away_from"

        return "stationary"