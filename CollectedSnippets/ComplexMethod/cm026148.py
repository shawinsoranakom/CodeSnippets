async def _async_update_data(self) -> ProximityData:
        """Calculate Proximity data."""
        if (zone_state := self.hass.states.get(self.proximity_zone_id)) is None:
            _LOGGER.debug(
                "%s: zone %s does not exist -> reset",
                self.name,
                self.proximity_zone_id,
            )
            return ProximityData(DEFAULT_PROXIMITY_DATA, {})

        entities_data = self.data.entities

        # calculate distance for all tracked entities
        for entity_id in self.tracked_entities:
            if (tracked_entity_state := self.hass.states.get(entity_id)) is None:
                if entities_data.pop(entity_id, None) is not None:
                    _LOGGER.debug(
                        "%s: %s does not exist -> remove", self.name, entity_id
                    )
                continue

            if entity_id not in entities_data:
                _LOGGER.debug("%s: %s is new -> add", self.name, entity_id)
                entities_data[entity_id] = {
                    ATTR_DIST_TO: None,
                    ATTR_DIR_OF_TRAVEL: None,
                    ATTR_NAME: tracked_entity_state.name,
                    ATTR_IN_IGNORED_ZONE: False,
                }
            entities_data[entity_id][ATTR_IN_IGNORED_ZONE] = (
                f"{ZONE_DOMAIN}.{tracked_entity_state.state.lower()}"
                in self.ignored_zone_ids
            )
            entities_data[entity_id][ATTR_DIST_TO] = self._calc_distance_to_zone(
                zone_state,
                tracked_entity_state,
                tracked_entity_state.attributes.get(ATTR_LATITUDE),
                tracked_entity_state.attributes.get(ATTR_LONGITUDE),
            )
            if entities_data[entity_id][ATTR_DIST_TO] is None:
                _LOGGER.debug(
                    "%s: %s has unknown distance got -> direction_of_travel=None",
                    self.name,
                    entity_id,
                )
                entities_data[entity_id][ATTR_DIR_OF_TRAVEL] = None

        # calculate direction of travel only for last updated tracked entity
        if (state_change_data := self.state_change_data) is not None and (
            new_state := state_change_data.new_state
        ) is not None:
            _LOGGER.debug(
                "%s: calculate direction of travel for %s",
                self.name,
                state_change_data.entity_id,
            )

            if (old_state := state_change_data.old_state) is not None:
                old_lat = old_state.attributes.get(ATTR_LATITUDE)
                old_lon = old_state.attributes.get(ATTR_LONGITUDE)
            else:
                old_lat = None
                old_lon = None

            entities_data[state_change_data.entity_id][ATTR_DIR_OF_TRAVEL] = (
                self._calc_direction_of_travel(
                    zone_state,
                    new_state,
                    old_lat,
                    old_lon,
                    new_state.attributes.get(ATTR_LATITUDE),
                    new_state.attributes.get(ATTR_LONGITUDE),
                )
            )

        # takeover data for legacy proximity entity
        proximity_data: dict[str, str | int | None] = {
            ATTR_DIST_TO: DEFAULT_DIST_TO_ZONE,
            ATTR_DIR_OF_TRAVEL: DEFAULT_DIR_OF_TRAVEL,
            ATTR_NEAREST: DEFAULT_NEAREST,
        }
        for entity_data in entities_data.values():
            if (distance_to := entity_data[ATTR_DIST_TO]) is None or entity_data[
                ATTR_IN_IGNORED_ZONE
            ]:
                continue

            if isinstance((nearest_distance_to := proximity_data[ATTR_DIST_TO]), str):
                _LOGGER.debug("set first entity_data: %s", entity_data)
                proximity_data = {
                    ATTR_DIST_TO: distance_to,
                    ATTR_DIR_OF_TRAVEL: entity_data[ATTR_DIR_OF_TRAVEL],
                    ATTR_NEAREST: str(entity_data[ATTR_NAME]),
                }
                continue

            if cast(int, nearest_distance_to) > int(distance_to):
                _LOGGER.debug("set closer entity_data: %s", entity_data)
                proximity_data = {
                    ATTR_DIST_TO: distance_to,
                    ATTR_DIR_OF_TRAVEL: entity_data[ATTR_DIR_OF_TRAVEL],
                    ATTR_NEAREST: str(entity_data[ATTR_NAME]),
                }
                continue

            if cast(int, nearest_distance_to) == int(distance_to):
                _LOGGER.debug("set equally close entity_data: %s", entity_data)
                proximity_data[ATTR_NEAREST] = (
                    f"{proximity_data[ATTR_NEAREST]}, {entity_data[ATTR_NAME]!s}"
                )

        return ProximityData(proximity_data, entities_data)