async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AdvantageAirDataConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AdvantageAir switch platform."""

    coordinator = config_entry.runtime_data

    entities: list[SwitchEntity] = []
    if aircons := coordinator.data.get("aircons"):
        for ac_key, ac_device in aircons.items():
            if ac_device["info"]["freshAirStatus"] != "none":
                entities.append(AdvantageAirFreshAir(coordinator, ac_key))
            if ADVANTAGE_AIR_AUTOFAN_ENABLED in ac_device["info"]:
                entities.append(AdvantageAirMyFan(coordinator, ac_key))
            if ADVANTAGE_AIR_NIGHT_MODE_ENABLED in ac_device["info"]:
                entities.append(AdvantageAirNightMode(coordinator, ac_key))
    if things := coordinator.data.get("myThings"):
        entities.extend(
            AdvantageAirRelay(coordinator, thing)
            for thing in things["things"].values()
            if thing["channelDipState"] == 8  # 8 = Other relay
        )
    async_add_entities(entities)