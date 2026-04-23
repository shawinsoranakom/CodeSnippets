def async_in_zones(
    hass: HomeAssistant, latitude: float, longitude: float, radius: float = 0
) -> tuple[State | None, list[str]]:
    """Find zones which contain the given latitude and longitude.

    Returns a tuple of the closest active zone and a list of all zones which
    contain the given latitude and longitude. The list of zones is sorted by
    distance and then by radius so that the closest and smallest zone is first.

    This method must be run in the event loop.
    """
    # Sort entity IDs so that we are deterministic if equal distance to 2 zones
    min_dist: float = sys.maxsize
    closest: State | None = None
    zones: list[tuple[str, float, float]] = []

    # This can be called before async_setup by device tracker
    zone_entity_ids = hass.data.get(DATA_ZONE_ENTITY_IDS, ())

    for entity_id in zone_entity_ids:
        if (
            not (zone := hass.states.get(entity_id))
            # Skip unavailable zones
            or zone.state == STATE_UNAVAILABLE
        ):
            continue
        zone_attrs = zone.attributes
        if (
            # Skip zones where we cannot calculate distance
            (
                zone_dist := distance(
                    latitude,
                    longitude,
                    zone_attrs[ATTR_LATITUDE],
                    zone_attrs[ATTR_LONGITUDE],
                )
            )
            is None
            # Skip zone that are outside the radius aka the
            # lat/long is outside the zone
            or not (zone_dist - (zone_radius := zone_attrs[ATTR_RADIUS]) < radius)
        ):
            continue

        zones.append((zone.entity_id, zone_dist, zone_radius))

        # Skip passive zones
        if zone_attrs.get(ATTR_PASSIVE):
            continue

        # If have a closest and its not closer than the closest skip it
        if closest and not (
            zone_dist < min_dist
            or (
                # If same distance, prefer smaller zone
                zone_dist == min_dist and zone_radius < closest.attributes[ATTR_RADIUS]
            )
        ):
            continue

        # We got here which means it closer than the previous known closest
        # or equal distance but this one is smaller.
        min_dist = zone_dist
        closest = zone

    # Sort by distance and then by radius so the closest and smallest zone is first.
    zones.sort(key=lambda x: (x[1], x[2]))
    return (closest, [itm[0] for itm in zones])