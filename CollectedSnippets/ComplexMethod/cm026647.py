async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyncConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Cync lights from a config entry."""

    coordinator = entry.runtime_data
    cync = coordinator.cync

    entities_to_add = []

    for home in cync.get_homes():
        for room in home.rooms:
            room_lights = [
                CyncLightEntity(device, coordinator, room.name)
                for device in room.devices
                if isinstance(device, CyncLight)
            ]
            entities_to_add.extend(room_lights)

            group_lights = [
                CyncLightEntity(device, coordinator, room.name)
                for group in room.groups
                for device in group.devices
                if isinstance(device, CyncLight)
            ]
            entities_to_add.extend(group_lights)

    async_add_entities(entities_to_add)