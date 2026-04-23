async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AdvantageAirDataConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AdvantageAir light platform."""

    coordinator = config_entry.runtime_data

    entities: list[LightEntity] = []
    if my_lights := coordinator.data.get("myLights"):
        for light in my_lights["lights"].values():
            if light.get("relay"):
                entities.append(AdvantageAirLight(coordinator, light))
            else:
                entities.append(AdvantageAirLightDimmable(coordinator, light))
    if things := coordinator.data.get("myThings"):
        for thing in things["things"].values():
            if thing["channelDipState"] == 4:  # 4 = "Light (on/off)""
                entities.append(AdvantageAirThingLight(coordinator, thing))
            elif thing["channelDipState"] == 5:  # 5 = "Light (Dimmable)""
                entities.append(AdvantageAirThingLightDimmable(coordinator, thing))
    async_add_entities(entities)