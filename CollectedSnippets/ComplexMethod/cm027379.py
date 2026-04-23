def zone(
    hass: HomeAssistant,
    zone_ent: str | State | None,
    entity: str | State | None,
) -> bool:
    """Test if zone-condition matches.

    Async friendly.
    """
    if zone_ent is None:
        raise ConditionErrorMessage("zone", "no zone specified")

    if isinstance(zone_ent, str):
        zone_ent_id = zone_ent

        if (zone_ent := hass.states.get(zone_ent)) is None:
            raise ConditionErrorMessage("zone", f"unknown zone {zone_ent_id}")

    if entity is None:
        raise ConditionErrorMessage("zone", "no entity specified")

    if isinstance(entity, str):
        entity_id = entity

        if (entity := hass.states.get(entity)) is None:
            raise ConditionErrorMessage("zone", f"unknown entity {entity_id}")
    else:
        entity_id = entity.entity_id

    if entity.state in (
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        return False

    latitude = entity.attributes.get(ATTR_LATITUDE)
    longitude = entity.attributes.get(ATTR_LONGITUDE)

    if latitude is None:
        raise ConditionErrorMessage(
            "zone", f"entity {entity_id} has no 'latitude' attribute"
        )

    if longitude is None:
        raise ConditionErrorMessage(
            "zone", f"entity {entity_id} has no 'longitude' attribute"
        )

    return in_zone(
        zone_ent, latitude, longitude, entity.attributes.get(ATTR_GPS_ACCURACY, 0)
    )