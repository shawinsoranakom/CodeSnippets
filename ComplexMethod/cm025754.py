async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AdvantageAirDataConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AdvantageAir cover platform."""

    coordinator = config_entry.runtime_data

    entities: list[CoverEntity] = []
    if aircons := coordinator.data.get("aircons"):
        for ac_key, ac_device in aircons.items():
            for zone_key, zone in ac_device["zones"].items():
                # Only add zone vent controls when zone in vent control mode.
                if zone["type"] == 0:
                    entities.append(AdvantageAirZoneVent(coordinator, ac_key, zone_key))
    if things := coordinator.data.get("myThings"):
        for thing in things["things"].values():
            if thing["channelDipState"] in [1, 2]:  # 1 = "Blind", 2 = "Blind 2"
                entities.append(
                    AdvantageAirThingCover(coordinator, thing, CoverDeviceClass.BLIND)
                )
            elif thing["channelDipState"] in [3, 10]:  # 3 & 10 = "Garage door"
                entities.append(
                    AdvantageAirThingCover(coordinator, thing, CoverDeviceClass.GARAGE)
                )
    async_add_entities(entities)