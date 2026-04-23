async def async_setup_entry(
    hass: HomeAssistant,
    entry: FreeboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    router = entry.runtime_data

    _LOGGER.debug("%s - %s - %s raid(s)", router.name, router.mac, len(router.raids))

    binary_entities: list[BinarySensorEntity] = [
        FreeboxRaidDegradedSensor(router, raid, description)
        for raid in router.raids.values()
        for description in RAID_SENSORS
    ]

    for node in router.home_devices.values():
        if node["category"] == FreeboxHomeCategory.PIR:
            binary_entities.append(FreeboxPirSensor(router, node))
        elif node["category"] == FreeboxHomeCategory.DWS:
            binary_entities.append(FreeboxDwsSensor(router, node))

        binary_entities.extend(
            FreeboxCoverSensor(router, node)
            for endpoint in node["show_endpoints"]
            if (
                endpoint["name"] == "cover"
                and endpoint["ep_type"] == "signal"
                and endpoint.get("value") is not None
            )
        )

    async_add_entities(binary_entities, True)